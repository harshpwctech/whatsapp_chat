<template>
  <div class="flex min-h-0 min-w-0 flex-col bg-[#e5ddd5]">
    <!-- Empty state -->
    <div
      v-if="!conversation"
      class="hidden flex-1 flex-col items-center justify-center px-6 text-center text-ink-gray-5 md:flex"
    >
      <div
        class="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-green-500 to-green-700 shadow-lg"
      >
        <FeatherIcon name="send" class="h-8 w-8 text-white" />
      </div>
      <h3 class="mb-1 text-lg font-medium text-ink-gray-8">
        {{ __('Select a conversation') }}
      </h3>
      <p class="text-sm">{{ __('Choose a contact from the list to start chatting') }}</p>
    </div>

    <template v-else>
      <!-- Header -->
      <div
        class="flex shrink-0 items-center justify-between gap-2 border-b border-outline-gray-2 bg-surface-white px-2 py-2 md:h-14 md:px-4 md:py-0"
        style="padding-top: max(0.5rem, env(safe-area-inset-top))"
      >
        <div class="flex min-w-0 flex-1 items-center gap-2">
          <button
            v-if="showBack"
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-ink-gray-7 active:bg-surface-gray-2 md:hidden"
            :aria-label="__('Back')"
            @click="$emit('back')"
          >
            <FeatherIcon name="arrow-left" class="h-5 w-5" />
          </button>
          <div
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-green-700 text-sm font-semibold text-white"
          >
            {{ initials(conversation.contact_name || conversation.mobile_no) }}
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-1.5">
              <p class="truncate text-sm font-semibold text-ink-gray-9">
                {{ conversation.contact_name || conversation.mobile_no }}
              </p>
              <Badge
                v-if="chatbotInstalled && detail?.is_transferred"
                theme="orange"
                variant="subtle"
                size="sm"
              >
                {{ __('Paused') }}
              </Badge>
              <Badge
                v-else-if="chatbotInstalled && detail?.has_bot_session"
                theme="blue"
                variant="subtle"
                size="sm"
                class="hidden sm:inline-flex"
              >
                {{ __('Bot Active') }}
              </Badge>
            </div>
            <p class="truncate text-xs text-ink-gray-5">{{ conversation.mobile_no }}</p>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-0.5">
          <Button
            variant="ghost"
            class="md:hidden"
            :aria-label="__('Contact info')"
            @click="$emit('open-info')"
          >
            <template #icon><FeatherIcon name="info" class="h-4 w-4" /></template>
          </Button>
          <Button
            v-if="chatbotInstalled && detail?.has_bot_session && !detail?.is_transferred"
            variant="solid"
            theme="green"
            size="sm"
            class="hidden sm:inline-flex"
            @click="$emit('transfer')"
          >
            {{ __('Transfer to Me') }}
          </Button>
          <Button
            v-if="chatbotInstalled && detail?.has_bot_session && !detail?.is_transferred"
            variant="solid"
            theme="green"
            size="sm"
            class="sm:hidden"
            :aria-label="__('Transfer to Me')"
            @click="$emit('transfer')"
          >
            <template #icon><FeatherIcon name="user-check" class="h-4 w-4" /></template>
          </Button>
          <Button
            v-if="chatbotInstalled && detail?.is_transferred"
            variant="outline"
            size="sm"
            class="hidden sm:inline-flex"
            @click="$emit('resume')"
          >
            <template #prefix><FeatherIcon name="play" class="h-3.5 w-3.5" /></template>
            {{ __('Resume Bot') }}
          </Button>
          <Button
            v-if="chatbotInstalled && detail?.is_transferred"
            variant="outline"
            size="sm"
            class="sm:hidden"
            :aria-label="__('Resume Bot')"
            @click="$emit('resume')"
          >
            <template #icon><FeatherIcon name="play" class="h-4 w-4" /></template>
          </Button>
        </div>
      </div>

      <!-- Messages -->
      <div
        ref="messagesEl"
        class="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-3 md:px-4 md:py-4"
      >
        <div v-if="loading" class="py-8 text-center text-sm text-ink-gray-5">
          {{ __('Loading messages...') }}
        </div>
        <template v-else>
          <template v-for="item in messageItems" :key="item.key">
            <div v-if="item.type === 'date'" class="my-3 flex justify-center">
              <span
                class="rounded-lg bg-white/90 px-3 py-1 text-xs font-medium text-ink-gray-6 shadow-sm"
              >
                {{ item.label }}
              </span>
            </div>
            <div
              v-else
              class="group mb-1 flex gap-1"
              :class="[
                isOutgoing(item.message) ? 'flex-row-reverse justify-start' : 'justify-start',
                item.message.reaction ? 'mb-7' : '',
              ]"
            >
              <div
                class="relative max-w-[88%] rounded-lg px-3 py-2 shadow-sm sm:max-w-[75%]"
                :class="[
                  isOutgoing(item.message)
                    ? 'rounded-tr-none bg-[#dcf8c6]'
                    : 'rounded-tl-none bg-white',
                  item.message.reaction ? 'mb-1' : '',
                ]"
              >
                <div
                  v-if="!isFailedStatus(item.message.status)"
                  class="absolute -right-1 -top-1 z-10 opacity-100 md:opacity-0 md:group-hover:opacity-100"
                >
                  <Dropdown :options="messageOptions(item.message)">
                    <button
                      type="button"
                      class="rounded-full bg-white p-1 shadow-sm"
                      :aria-label="__('Message options')"
                    >
                      <FeatherIcon name="chevron-down" class="h-3.5 w-3.5 text-ink-gray-5" />
                    </button>
                  </Dropdown>
                </div>
                <WhatsAppMessage :message="item.message" />
                <div class="mt-1 flex items-end justify-end gap-1 text-ink-gray-5">
                  <span
                    class="text-[10px] leading-none"
                    :title="formatMessageDateTime(item.message.creation)"
                  >
                    {{ formatMessageTime(item.message.creation) }}
                  </span>
                  <MessageStatus v-if="isOutgoing(item.message)" :status="item.message.status" />
                </div>
                <div
                  v-if="item.message.reaction"
                  class="absolute -bottom-4 z-10 flex rounded-full border border-outline-gray-2 bg-white px-1.5 py-0.5 text-sm shadow-sm"
                  :class="isOutgoing(item.message) ? 'right-2' : 'left-2'"
                >
                  {{ item.message.reaction }}
                </div>
              </div>
              <div
                v-if="!isFailedStatus(item.message.status)"
                class="flex items-center self-center opacity-100 md:opacity-0 md:group-hover:opacity-100"
              >
                <EmojiPicker v-model="reactionEmoji" v-model:reaction="reactionMode">
                  <template #default="{ togglePopover }">
                    <button
                      type="button"
                      class="flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm"
                      :aria-label="__('React')"
                      @click="startReaction(item.message.name, togglePopover)"
                    >
                      <ReactIcon class="text-ink-gray-4" />
                    </button>
                  </template>
                </EmojiPicker>
              </div>
            </div>
          </template>
        </template>
      </div>

      <!-- Reply preview -->
      <div
        v-if="replyTo"
        class="flex items-center gap-2 border-t border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
      >
        <div
          class="min-w-0 flex-1 rounded border-0 border-l-4 bg-white p-2 text-sm"
          :class="replyTo.type === 'Incoming' ? 'border-green-500' : 'border-blue-400'"
        >
          <div class="mb-0.5 text-xs font-semibold text-ink-gray-7">
            {{ replyTo.from_name || (replyTo.type === 'Incoming' ? conversation?.contact_name : __('You')) }}
          </div>
          <div class="truncate text-ink-gray-6">{{ replyPreviewText(replyTo) }}</div>
        </div>
        <Button variant="ghost" @click="replyTo = null">
          <template #icon><FeatherIcon name="x" class="h-4 w-4" /></template>
        </Button>
      </div>

      <!-- Input -->
      <div
        class="safe-bottom flex shrink-0 items-end gap-2 border-t border-outline-gray-2 bg-surface-gray-1 px-3 py-2 md:px-4 md:py-3"
      >
        <EmojiPicker v-model="composeEmoji" :reaction="false">
          <template #default="{ togglePopover }">
            <button
              type="button"
              class="flex h-10 w-10 shrink-0 items-center justify-center text-ink-gray-5"
              :aria-label="__('Insert emoji')"
              @click="togglePopover"
            >
              <SmileIcon />
            </button>
          </template>
        </EmojiPicker>
        <textarea
          ref="draftInput"
          v-model="draft"
          rows="1"
          class="max-h-32 min-h-[44px] flex-1 resize-none rounded-2xl border border-outline-gray-2 bg-surface-white px-4 py-2.5 text-base leading-snug focus:border-green-500 focus:outline-none md:min-h-[36px] md:text-sm"
          :placeholder="__('Type a message...')"
          @keydown="onDraftKeydown"
        />
        <button
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-green-600 text-white transition-colors active:bg-green-800 hover:bg-green-700 disabled:opacity-50 md:h-10 md:w-10"
          :disabled="sending || !draft.trim()"
          :aria-label="__('Send')"
          @click="submit"
        >
          <FeatherIcon name="send" class="h-4 w-4" />
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Dropdown } from 'frappe-ui'
import WhatsAppMessage from './WhatsAppMessage.vue'
import MessageStatus from './MessageStatus.vue'
import EmojiPicker from './EmojiPicker.vue'
import ReactIcon from '@/components/icons/ReactIcon.vue'
import SmileIcon from '@/components/icons/SmileIcon.vue'
import {
  formatMessageDateTime,
  formatMessageTime,
  isFailedStatus,
  messageDateKey,
} from '@/utils/whatsappMessage.js'
import { useChatbotInstalled } from '@/composables/useChatbot.js'

const __ = window.__ || ((s) => s)
const chatbotInstalled = useChatbotInstalled()

const props = defineProps({
  conversation: { type: Object, default: null },
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  sending: { type: Boolean, default: false },
  detail: { type: Object, default: null },
  showBack: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'transfer', 'resume', 'assign', 'back', 'open-info', 'react'])

const draft = ref('')
const draftInput = ref(null)
const messagesEl = ref(null)
const replyTo = ref(null)
const reactionEmoji = ref('')
const reactionMode = ref(true)
const reactionTarget = ref(null)
const composeEmoji = ref('')

const messageItems = computed(() => {
  const items = []
  let lastDate = ''

  for (const message of props.messages) {
    const dateKey = messageDateKey(message.creation)
    if (dateKey && dateKey !== lastDate) {
      items.push({ type: 'date', key: `date-${dateKey}`, label: dateKey })
      lastDate = dateKey
    }
    items.push({
      type: 'message',
      key: message.name || `msg-${message.creation}-${message.message}`,
      message,
    })
  }

  return items
})

function isOutgoing(msg) {
  if (msg.type === 'Outgoing') return true
  if (msg.type === 'Incoming') return false
  return msg.sender_user_no === 'Administrator'
}

function initials(name) {
  if (!name) return '?'
  return String(name).substring(0, 2).toUpperCase()
}

function submit() {
  if (!draft.value.trim()) return
  emit('send', { content: draft.value.trim(), reply_to: replyTo.value?.name || '' })
  draft.value = ''
  replyTo.value = null
  nextTick(resizeDraft)
}

function onDraftKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}

function resizeDraft() {
  const el = draftInput.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 128)}px`
}

function replyPreviewText(message) {
  if (message.message_type === 'Template') {
    return (message.template || message.template_name || __('Template message')).slice(0, 120)
  }
  if (message.attach) return __('Attachment')
  return (message.message || '').slice(0, 120)
}

function messageOptions(message) {
  return [
    {
      label: __('Reply'),
      onClick: () => {
        replyTo.value = message
        nextTick(() => draftInput.value?.focus())
      },
    },
  ]
}

function startReaction(messageName, togglePopover) {
  reactionTarget.value = messageName
  reactionMode.value = true
  togglePopover()
}

watch(reactionEmoji, (emoji) => {
  if (!emoji || !reactionTarget.value) return
  emit('react', { name: reactionTarget.value, emoji })
  reactionEmoji.value = ''
  reactionTarget.value = null
})

watch(composeEmoji, (emoji) => {
  if (!emoji) return
  draft.value += emoji
  composeEmoji.value = ''
  nextTick(() => {
    draftInput.value?.focus()
    resizeDraft()
  })
})

watch(draft, () => {
  nextTick(resizeDraft)
})

watch(
  () => props.conversation?.mobile_no,
  () => {
    replyTo.value = null
  },
)

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  },
)
</script>
