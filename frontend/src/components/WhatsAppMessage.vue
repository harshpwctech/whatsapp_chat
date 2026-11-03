<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    :id="message.name"
    class="group/message relative"
  >
    <Badge
      v-if="isFailedStatus(message.status)"
      theme="red"
      :label="message.status"
      class="absolute -top-2 right-0 z-10"
    />

    <div
      v-if="message.is_reply"
      class="mb-1.5 cursor-pointer rounded border-0 border-l-4 bg-black/5 p-2 text-ink-gray-5"
      :class="
        message.reply_to_type === 'Incoming'
          ? 'border-green-500'
          : 'border-blue-400'
      "
      @click="scrollToReply(message.reply_to)"
    >
      <div
        class="mb-1 text-xs font-bold"
        :class="
          message.reply_to_type === 'Incoming'
            ? 'text-green-700'
            : 'text-blue-600'
        "
      >
        {{ message.reply_to_from || __('You') }}
      </div>
      <div class="max-h-12 overflow-hidden text-sm">
        <img
          v-if="isHeaderImage(message) && message.header_media"
          :src="message.header_media"
          class="mb-1 max-h-10 rounded object-cover"
          alt=""
        />
        <div v-else-if="message.header" class="font-semibold">{{ message.header }}</div>
        <div v-if="message.reply_message" v-html="formatWhatsAppMessage(message.reply_message)" />
        <div v-if="message.footer" class="text-xs text-ink-gray-5">{{ message.footer }}</div>
      </div>
    </div>

    <div v-if="message.message_type === 'Template'" class="flex flex-col gap-1.5">
      <img
        v-if="isHeaderImage(message) && message.header_media"
        :src="message.header_media"
        class="-mx-1 -mt-1 mb-1 max-h-48 w-[calc(100%+0.5rem)] cursor-pointer rounded-t-md object-cover"
        alt=""
        @click="openFile(message.header_media)"
      />
      <div
        v-else-if="isHeaderDocument(message) && message.header_media"
        class="flex cursor-pointer items-center gap-2 rounded-md bg-black/5 p-2"
        @click="openFile(message.header_media)"
      >
        <DocumentIcon class="!h-8 !w-8" />
        <div class="text-sm text-ink-gray-6">{{ headerDocumentLabel }}</div>
      </div>
      <div v-else-if="message.header" class="text-sm font-semibold">{{ message.header }}</div>
      <div class="text-sm" v-html="formatWhatsAppMessage(message.template)" />
      <div v-if="message.footer" class="text-xs text-ink-gray-5">{{ message.footer }}</div>
    </div>

    <div v-else-if="message.content_type === 'text'">
      <div
        v-if="isContactMessage(message)"
        class="flex items-start gap-2 rounded-md border border-outline-gray-2 bg-surface-gray-1 p-2"
      >
        <FeatherIcon name="user" class="mt-0.5 h-4 w-4 shrink-0 text-ink-gray-5" />
        <div class="min-w-0 text-sm">
          <div class="font-semibold text-ink-gray-9">{{ contactInfo.name }}</div>
          <div v-if="contactInfo.phones" class="text-ink-gray-6">{{ contactInfo.phones }}</div>
        </div>
      </div>
      <div v-else class="text-sm" v-html="formatWhatsAppMessage(message.message)" />
    </div>

    <div v-else-if="['button', 'interactive'].includes(message.content_type)">
      <div class="text-sm" v-html="formatWhatsAppMessage(message.message)" />
      <div
        v-if="buttons.length"
        class="mt-2 flex flex-col gap-1 border-t border-gray-200 pt-1.5"
      >
        <div
          v-for="button in buttons"
          :key="button.id || button.title"
          class="rounded py-1 text-center text-sm font-medium text-blue-600"
        >
          {{ button.title }}
        </div>
      </div>
    </div>

    <div v-else-if="message.content_type === 'image'">
      <img
        :src="message.attach"
        class="max-h-48 cursor-pointer rounded-md"
        alt=""
        @click="openFile(message.attach)"
      />
      <div
        v-if="message.message && !message.message.startsWith('/files/')"
        class="mt-1.5 text-sm"
        v-html="formatWhatsAppMessage(message.message)"
      />
    </div>

    <div
      v-else-if="message.content_type === 'document'"
      class="flex cursor-pointer items-center gap-2"
      @click="openFile(message.attach)"
    >
      <DocumentIcon />
      <div class="text-sm text-ink-gray-6">{{ documentLabel }}</div>
    </div>

    <div v-else-if="message.content_type === 'audio'" class="flex items-center gap-2">
      <audio :src="message.attach" controls class="max-w-full" />
    </div>

    <div v-else-if="message.content_type === 'video'">
      <video :src="message.attach" controls class="max-h-48 rounded-md" />
      <div
        v-if="message.message && !message.message.startsWith('/files/')"
        class="mt-1.5 text-sm"
        v-html="formatWhatsAppMessage(message.message)"
      />
    </div>

    <div
      v-else-if="message.attach"
      class="flex cursor-pointer items-center gap-2"
      @click="openFile(message.attach)"
    >
      <DocumentIcon />
      <div class="text-sm text-ink-gray-6">{{ __('Attachment') }}</div>
    </div>

    <div
      v-else
      class="text-sm"
      v-html="formatWhatsAppMessage(message.message || message.template)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Badge, FeatherIcon } from 'frappe-ui'
import DocumentIcon from '@/components/icons/DocumentIcon.vue'
import {
  formatWhatsAppMessage,
  isContactMessage,
  isFailedStatus,
  isHeaderDocument,
  isHeaderImage,
  parseButtons,
  parseContactMessage,
} from '@/utils/whatsappMessage.js'

const __ = window.__ || ((s) => s)

const props = defineProps({
  message: { type: Object, required: true },
})

const buttons = computed(() => parseButtons(props.message.buttons))

const contactInfo = computed(() => parseContactMessage(props.message))

const documentLabel = computed(() => {
  const attach = props.message.attach || ''
  const name = attach.split('/').pop()
  return name || __('Document')
})

const headerDocumentLabel = computed(() => {
  if (props.message.header_filename) return props.message.header_filename
  const attach = props.message.header_media || ''
  const name = attach.split('/').pop()
  return name || __('Document')
})

function openFile(url) {
  if (url) window.open(url, '_blank')
}

function scrollToReply(name) {
  if (!name) return
  const element = document.getElementById(name)
  if (!element) return
  element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  element.classList.add('ring-2', 'ring-yellow-300')
  setTimeout(() => {
    element.classList.remove('ring-2', 'ring-yellow-300')
  }, 1200)
}
</script>
