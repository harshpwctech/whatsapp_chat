<template>
  <div class="flex h-full min-h-0 bg-surface-gray-1">
    <ConversationList
      class="h-full shrink-0"
      :class="listPanelClass"
      :items="inboxItems"
      :selected="selected"
      :tab="tab"
      :loading="inboxLoading"
      :loading-more="inboxLoadingMore"
      :has-more="inboxHasMore"
      :search="search"
      @update:tab="setTab"
      @update:search="onSearchChange"
      @select="selectConversation"
      @refresh="reloadInbox"
      @load-more="loadMoreInbox"
    />

    <ChatThread
      class="min-h-0 min-w-0 flex-1"
      :class="chatPanelClass"
      :conversation="selected"
      :messages="messages"
      :loading="messagesLoading"
      :sending="sending"
      :detail="detail"
      :show-back="isMobile && !!selected"
      @back="goBackToList"
      @open-info="showSessionMobile = true"
      @send="sendMessage"
      @react="reactOnMessage"
      @transfer="transferToMe"
      @resume="resumeChatbot"
      @assign="openAssign"
    />

    <SessionPanel
      v-if="selected && !isMobile"
      :conversation="selected"
      :detail="detail"
      @transfer="transferToMe"
      @resume="resumeChatbot"
      @assign="openAssign"
    />

    <Dialog
      v-if="isMobile"
      v-model="showSessionMobile"
      :options="{ title: __('Contact Info'), size: 'lg' }"
    >
      <template #body-content>
        <SessionPanel
          v-if="selected"
          embedded
          :conversation="selected"
          :detail="detail"
          @transfer="onMobileTransfer"
          @resume="onMobileResume"
          @assign="onMobileAssign"
        />
      </template>
    </Dialog>

    <Dialog v-model="showAssign" :options="{ title: __('Assign Agent'), size: 'sm' }">
      <template #body-content>
        <div class="p-2">
          <Link
            v-model="assignAgent"
            doctype="User"
            :label="__('Agent')"
            :placeholder="__('Select user')"
            :filters="assignAgentFilters"
            variant="outline"
          />
          <button
            v-if="assignAgent"
            type="button"
            class="mt-2 text-xs text-ink-gray-5 hover:text-ink-gray-7"
            @click="assignAgent = ''"
          >
            {{ __('Clear assignment') }}
          </button>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" theme="green" :loading="assigning" @click="assignContact">
          {{ __('Assign') }}
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, ref, watch } from 'vue'
import { Dialog, createResource, frappeRequest, toast } from 'frappe-ui'
import { Link } from 'frappe-ui/frappe'
import ConversationList from '@/components/ConversationList.vue'
import ChatThread from '@/components/ChatThread.vue'
import SessionPanel from '@/components/SessionPanel.vue'
import { useIsMobile } from '@/composables/useMediaQuery.js'
import {
  playNotificationSound,
  playReceiveSound,
  playSendSound,
} from '@/utils/notificationSound.js'

const __ = window.__ || ((s) => s)
const socket = inject('socket')
const isMobile = useIsMobile()

const tab = ref('all')
const search = ref('')
const selected = ref(null)
const messages = ref([])
const messagesLoading = ref(false)
const sending = ref(false)
const detail = ref(null)
const showAssign = ref(false)
const showSessionMobile = ref(false)
const assignAgent = ref('')
const assigning = ref(false)

const assignableAgents = createResource({
  url: 'whatsapp_chat.api.inbox.get_assignable_agents',
  auto: false,
})

const assignAgentFilters = computed(() => {
  const names = (assignableAgents.data || []).map((user) => user.value)
  return {
    enabled: 1,
    user_type: 'System User',
    name: ['in', names.length ? names : ['__none__']],
  }
})

const inboxItems = ref([])
const inboxPage = ref(1)
const inboxHasMore = ref(false)
const inboxLoading = ref(false)
const inboxLoadingMore = ref(false)
let searchTimer = null

async function fetchInbox(page = 1, append = false) {
  if (append) {
    if (inboxLoadingMore.value || inboxLoading.value || !inboxHasMore.value) return
    inboxLoadingMore.value = true
  } else {
    inboxLoading.value = true
    inboxPage.value = 1
    inboxHasMore.value = false
  }

  try {
    const data = await frappeRequest({
      url: '/api/method/whatsapp_chat.api.inbox.get_inbox',
      params: {
        tab: tab.value,
        search: search.value.trim() || undefined,
        page,
      },
    })
    const items = Array.isArray(data) ? data : data?.items || []
    const hasMore = Array.isArray(data) ? false : !!data?.has_more

    inboxItems.value = append ? [...inboxItems.value, ...items] : items
    inboxPage.value = page
    inboxHasMore.value = hasMore
  } catch (e) {
    if (!append) inboxItems.value = []
    toast.error(__('Failed to load conversations'))
  } finally {
    inboxLoading.value = false
    inboxLoadingMore.value = false
  }
}

function loadMoreInbox() {
  fetchInbox(inboxPage.value + 1, true)
}

const listPanelClass = computed(() => {
  if (!isMobile.value) return 'w-80 min-w-80'
  return selected.value ? 'hidden' : 'w-full'
})

const chatPanelClass = computed(() => {
  if (!isMobile.value) return ''
  return selected.value ? 'flex w-full' : 'hidden'
})

function setTab(newTab) {
  tab.value = newTab
  selected.value = null
  messages.value = []
  detail.value = null
  showSessionMobile.value = false
  fetchInbox(1)
}

function onSearchChange(value) {
  search.value = value
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchInbox(1)
  }, 300)
}

function reloadInbox() {
  fetchInbox(1)
}

function goBackToList() {
  selected.value = null
  messages.value = []
  detail.value = null
  showSessionMobile.value = false
}

async function selectConversation(item) {
  selected.value = item
  await loadMessages(item)
  await loadDetail(item)
  if (item.name) markRead(item.name)
}

async function loadMessages(item) {
  messagesLoading.value = true
  try {
    messages.value = await frappeRequest({
      url: '/api/method/whatsapp_chat.api.message.get_all',
      params: { room: item.name || '', user_no: item.mobile_no },
    })
  } catch (e) {
    toast.error(__('Failed to load messages'))
    messages.value = []
  } finally {
    messagesLoading.value = false
  }
}

async function loadDetail(item) {
  try {
    detail.value = await frappeRequest({
      url: '/api/method/whatsapp_chat.api.inbox.get_conversation_detail',
      params: { phone_number: item.mobile_no },
    })
  } catch (e) {
    detail.value = null
  }
}

async function sendMessage(payload) {
  const content = typeof payload === 'string' ? payload : payload?.content
  const replyTo = typeof payload === 'object' ? payload?.reply_to : ''
  if (!selected.value || !content?.trim()) return
  sending.value = true
  const item = selected.value

  try {
    await frappeRequest({
      url: '/api/method/whatsapp_chat.api.message.send',
      params: {
        content: content.trim(),
        user: window.user,
        room: item.name || '',
        user_no: item.mobile_no,
        reply_to: replyTo || undefined,
      },
    })
    await loadMessages(item)
    playSendSound()
  } catch (e) {
    toast.error(__('Failed to send message'))
  } finally {
    sending.value = false
  }
}

async function reactOnMessage({ name, emoji }) {
  if (!name || !emoji) return
  try {
    await frappeRequest({
      url: '/api/method/whatsapp_chat.api.message.react_on_message',
      params: { reply_to_name: name, emoji },
    })
    if (selected.value) await loadMessages(selected.value)
  } catch (e) {
    toast.error(__('Failed to add reaction'))
  }
}

async function transferToMe() {
  if (!selected.value) return
  const session = detail.value?.bot_session
  try {
    await frappeRequest({
      url: '/api/method/whatsapp_chat.api.inbox.transfer_to_agent',
      params: {
        phone_number: selected.value.mobile_no,
        whatsapp_account: session?.whatsapp_account,
        agent: window.user,
      },
    })
    toast.success(__('Conversation transferred to you'))
    reloadInbox()
    await loadDetail(selected.value)
  } catch (e) {
    toast.error(__('Transfer failed'))
  }
}

async function resumeChatbot() {
  if (!selected.value) return
  try {
    await frappeRequest({
      url: '/api/method/whatsapp_chat.api.inbox.resume_chatbot',
      params: { phone_number: selected.value.mobile_no },
    })
    toast.success(__('Chatbot resumed'))
    reloadInbox()
    await loadDetail(selected.value)
  } catch (e) {
    toast.error(__('Failed to resume chatbot'))
  }
}

function openAssign() {
  assignAgent.value = selected.value?.email || window.user || ''
  assignableAgents.fetch()
  showAssign.value = true
}

async function assignContact() {
  if (!selected.value?.name) return
  assigning.value = true
  try {
    await frappeRequest({
      url: '/api/method/whatsapp_chat.api.inbox.assign_contact',
      params: { contact_name: selected.value.name, agent: assignAgent.value },
    })
    toast.success(__('Agent assigned'))
    showAssign.value = false
    selected.value.email = assignAgent.value
    reloadInbox()
    await loadDetail(selected.value)
  } catch (e) {
    toast.error(__('Assignment failed'))
  } finally {
    assigning.value = false
  }
}

function onMobileTransfer() {
  showSessionMobile.value = false
  transferToMe()
}

function onMobileResume() {
  showSessionMobile.value = false
  resumeChatbot()
}

function onMobileAssign() {
  showSessionMobile.value = false
  openAssign()
}

function markRead(room) {
  frappeRequest({
    url: '/api/method/whatsapp_chat.api.message.mark_as_read',
    params: { room },
  })
}

function onInboxUpdate(data) {
  if (data.type === 'transfer' || data.type === 'resume') {
    reloadInbox()
    if (selected.value) loadDetail(selected.value)
    return
  }

  const isCurrentChat =
    selected.value &&
    ((data.room && selected.value.name === data.room) ||
      (data.mobile_no &&
        normalizePhone(data.mobile_no) === normalizePhone(selected.value.mobile_no)))

  const isIncoming = data.type === 'Incoming'

  if (isIncoming) {
    if (isCurrentChat) {
      playReceiveSound()
    } else {
      playNotificationSound()
    }
  }

  if (isCurrentChat) {
    loadMessages(selected.value)
    if (data.room) markRead(data.room)
  }
  reloadInbox()
}

function normalizePhone(phone) {
  return String(phone || '').replace(/\D/g, '').slice(-10)
}

onMounted(() => {
  if (!window.chatbot_installed && tab.value !== 'all') {
    tab.value = 'all'
  }
  fetchInbox(1)
  socket?.on('whatsapp_inbox_update', onInboxUpdate)
})

onUnmounted(() => {
  socket?.off('whatsapp_inbox_update', onInboxUpdate)
})

watch(tab, () => {
  selected.value = null
  messages.value = []
  detail.value = null
  showSessionMobile.value = false
})
</script>
