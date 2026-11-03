<template>
  <div
    class="flex w-72 min-w-72 flex-col border-l border-outline-gray-2 bg-surface-white"
    :class="{ '!w-full !min-w-0 !border-l-0': embedded }"
  >
    <div v-if="!embedded" class="border-b border-outline-gray-2 p-4">
      <h3 class="text-sm font-semibold uppercase tracking-wide text-ink-gray-5">
        {{ __('Contact Info') }}
      </h3>
    </div>

    <div class="flex-1 overflow-y-auto p-4" :class="{ 'pt-0': embedded }">
      <div class="mb-6 text-center">
        <div
          class="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-green-700 text-xl font-semibold text-white"
        >
          {{ initials(conversation.contact_name || conversation.mobile_no) }}
        </div>
        <p class="font-medium text-ink-gray-9">
          {{ conversation.contact_name || conversation.mobile_no }}
        </p>
        <p class="text-sm text-ink-gray-5">{{ conversation.mobile_no }}</p>
      </div>

      <div class="mb-4 space-y-2 text-sm">
        <div class="flex justify-between gap-3">
          <span class="shrink-0 text-ink-gray-5">{{ __('Assigned') }}</span>
          <span class="text-right font-medium text-ink-gray-8">
            {{ conversation.email || __('Unassigned') }}
          </span>
        </div>
      </div>

      <div v-if="chatbotInstalled && detail?.bot_session" class="mb-4 rounded-lg border border-outline-gray-2 p-3">
        <h4 class="mb-2 text-xs font-semibold uppercase text-ink-gray-5">
          {{ __('Chatbot Session') }}
        </h4>
        <div class="space-y-1.5 text-sm">
          <div class="flex justify-between gap-2">
            <span class="text-ink-gray-5">{{ __('Flow') }}</span>
            <span class="text-right font-medium">
              {{ detail.bot_session.current_flow_title || detail.bot_session.current_flow || '-' }}
            </span>
          </div>
          <div class="flex justify-between gap-2">
            <span class="text-ink-gray-5">{{ __('Step') }}</span>
            <span class="text-right font-medium">
              {{ detail.bot_session.current_step || '-' }}
            </span>
          </div>
          <div class="flex justify-between gap-2">
            <span class="text-ink-gray-5">{{ __('Last Activity') }}</span>
            <span class="text-right font-medium">
              {{ formatDt(detail.bot_session.last_activity) }}
            </span>
          </div>
        </div>
      </div>

      <div
        v-if="chatbotInstalled && detail?.transfer"
        class="mb-4 rounded-lg border border-orange-200 bg-orange-50 p-3"
      >
        <h4 class="mb-2 text-xs font-semibold uppercase text-orange-700">
          {{ __('Agent Transfer') }}
        </h4>
        <div class="space-y-1.5 text-sm">
          <div class="flex justify-between gap-2">
            <span class="text-ink-gray-5">{{ __('Agent') }}</span>
            <span class="font-medium">
              {{ detail.transfer.agent_name || detail.transfer.agent }}
            </span>
          </div>
          <div class="flex justify-between gap-2">
            <span class="text-ink-gray-5">{{ __('Transferred') }}</span>
            <span class="font-medium">{{ formatDt(detail.transfer.transferred_at) }}</span>
          </div>
        </div>
      </div>

      <div class="space-y-2">
        <Button
          v-if="chatbotInstalled && detail?.has_bot_session && !detail?.is_transferred"
          class="w-full"
          variant="solid"
          theme="green"
          @click="$emit('transfer')"
        >
          {{ __('Transfer to Me') }}
        </Button>
        <Button
          v-if="chatbotInstalled && detail?.is_transferred"
          class="w-full"
          variant="outline"
          @click="$emit('resume')"
        >
          {{ __('Resume Chatbot') }}
        </Button>
        <Button
          v-if="conversation.name"
          class="w-full"
          variant="outline"
          @click="$emit('assign')"
        >
          {{ __('Assign Agent') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { useChatbotInstalled } from '@/composables/useChatbot.js'

const __ = window.__ || ((s) => s)
const chatbotInstalled = useChatbotInstalled()

defineProps({
  conversation: { type: Object, required: true },
  detail: { type: Object, default: null },
  embedded: { type: Boolean, default: false },
})

defineEmits(['transfer', 'resume', 'assign'])

function initials(name) {
  if (!name) return '?'
  return String(name).substring(0, 2).toUpperCase()
}

function formatDt(dt) {
  if (!dt) return '-'
  const parsed = dayjs(dt)
  return parsed.isValid() ? parsed.format('MMM D, YYYY hh:mm A') : '-'
}
</script>
