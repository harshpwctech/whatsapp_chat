<template>
  <div
    class="flex flex-col border-r border-outline-gray-2 bg-surface-white"
  >
    <div class="shrink-0 border-b border-outline-gray-2 p-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <div class="mb-3 flex items-center justify-between">
        <h2 class="text-base font-semibold text-ink-gray-9">{{ __('WhatsApp') }}</h2>
        <Button variant="ghost" @click="$emit('refresh')">
          <template #icon><FeatherIcon name="refresh-cw" class="h-4 w-4" /></template>
        </Button>
      </div>
      <div class="relative mb-3">
        <FeatherIcon
          name="search"
          class="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-gray-5"
        />
        <input
          :value="search"
          class="h-10 w-full rounded-lg border border-outline-gray-2 bg-surface-gray-1 pl-8 pr-3 text-base md:h-8 md:text-sm"
          :placeholder="__('Search conversations...')"
          @input="$emit('update:search', $event.target.value)"
        />
      </div>
      <div class="flex gap-1 overflow-x-auto pb-0.5">
        <button
          v-for="t in tabs"
          :key="t.id"
          class="shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-colors md:py-1"
          :class="
            tab === t.id
              ? 'bg-green-600 text-white'
              : 'bg-surface-gray-2 text-ink-gray-6 hover:bg-surface-gray-3'
          "
          @click="$emit('update:tab', t.id)"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <div ref="listEl" class="min-h-0 flex-1 overflow-y-auto overscroll-contain" @scroll="onScroll">
      <div v-if="loading && !items.length" class="p-6 text-center text-sm text-ink-gray-5">
        {{ __('Loading...') }}
      </div>
      <div v-else-if="!items.length" class="p-6 text-center text-sm text-ink-gray-5">
        <FeatherIcon name="message-circle" class="mx-auto mb-2 h-8 w-8 opacity-40" />
        {{ __('No conversations') }}
      </div>
      <button
        v-for="item in items"
        :key="item.name || item.mobile_no"
        class="flex w-full items-start gap-3 border-b border-outline-gray-1 px-3 py-3.5 text-left transition-colors active:bg-surface-gray-2 hover:bg-surface-gray-1 md:py-3"
        :class="isSelected(item) ? 'bg-surface-gray-2' : ''"
        @click="$emit('select', item)"
      >
        <div
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-green-700 text-sm font-semibold text-white md:h-10 md:w-10"
        >
          {{ initials(item.contact_name || item.mobile_no) }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-2">
            <p class="truncate text-sm font-medium text-ink-gray-9">
              {{ item.contact_name || item.mobile_no }}
            </p>
            <span class="shrink-0 text-[11px] text-ink-gray-5">
              {{ formatTime(item.modified) }}
            </span>
          </div>
          <p class="truncate text-xs text-ink-gray-5">
            {{ item.last_message || item.current_flow_title || item.mobile_no }}
          </p>
          <div class="mt-1 flex flex-wrap gap-1">
            <Badge v-if="!item.is_read" theme="green" variant="subtle" size="sm">
              {{ __('New') }}
            </Badge>
            <Badge
              v-if="chatbotInstalled && item.has_bot_session && !item.is_transferred"
              theme="blue"
              variant="subtle"
              size="sm"
            >
              {{ __('Bot') }}
            </Badge>
            <Badge v-if="chatbotInstalled && item.is_transferred" theme="orange" variant="subtle" size="sm">
              {{ __('Agent') }}
            </Badge>
          </div>
        </div>
      </button>
      <div v-if="loadingMore" class="p-4 text-center text-xs text-ink-gray-5">
        {{ __('Loading more...') }}
      </div>
      <div v-else-if="hasMore && items.length" class="p-3 text-center">
        <button
          type="button"
          class="text-xs font-medium text-green-700 hover:text-green-800"
          @click="$emit('load-more')"
        >
          {{ __('Load more conversations') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatPrettyDate } from '@/utils/whatsappMessage.js'
import { useChatbotInstalled } from '@/composables/useChatbot.js'

const __ = window.__ || ((s) => s)
const chatbotInstalled = useChatbotInstalled()
const listEl = ref(null)

const props = defineProps({
  items: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  tab: { type: String, default: 'all' },
  loading: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: false },
  search: { type: String, default: '' },
})

const emit = defineEmits(['update:tab', 'update:search', 'select', 'refresh', 'load-more'])

const tabs = computed(() => {
  const list = [{ id: 'all', label: __('All') }]
  if (chatbotInstalled.value) {
    list.push({ id: 'bot', label: __('Bot') }, { id: 'transferred', label: __('Agent') })
  }
  return list
})

function isSelected(item) {
  if (!props.selected) return false
  if (props.selected.name && item.name) return props.selected.name === item.name
  return props.selected.mobile_no === item.mobile_no
}

function initials(name) {
  if (!name) return '?'
  const parts = String(name)
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .trim()
    .split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return String(name).substring(0, 2).toUpperCase()
}

function formatTime(dt) {
  return formatPrettyDate(dt)
}

function onScroll() {
  const el = listEl.value
  if (!el || !props.hasMore || props.loadingMore || props.loading) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 120) {
    emit('load-more')
  }
}
</script>
