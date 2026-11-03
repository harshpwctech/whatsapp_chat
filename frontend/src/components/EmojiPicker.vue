<template>
  <Popover>
    <template #target="{ togglePopover, isOpen }">
      <slot :toggle-popover="togglePopover" :is-open="isOpen" />
    </template>
    <template #body="{ togglePopover }">
      <div
        v-if="reaction"
        class="flex items-center justify-center gap-2 rounded-full bg-white px-2 py-1 shadow-lg ring-1 ring-black/5"
      >
        <button
          v-for="item in reactionEmojis"
          :key="item"
          type="button"
          class="text-xl leading-none"
          @click="select(item, togglePopover)"
        >
          {{ item }}
        </button>
      </div>
      <div
        v-else
        class="grid max-h-48 w-64 grid-cols-8 gap-1 overflow-y-auto rounded-lg bg-white p-2 shadow-lg ring-1 ring-black/5"
      >
        <button
          v-for="item in composeEmojis"
          :key="item"
          type="button"
          class="rounded p-1 text-lg hover:bg-surface-gray-2"
          @click="select(item, togglePopover)"
        >
          {{ item }}
        </button>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Popover } from 'frappe-ui'

const model = defineModel({ type: String, default: '' })
const reaction = defineModel('reaction', { type: Boolean, default: false })

const reactionEmojis = ['👍', '❤️', '😂', '😮', '😢', '🙏']
const composeEmojis = [
  '😀', '😁', '😂', '🤣', '😊', '😍', '😘', '😎',
  '🙂', '😉', '😢', '😭', '😡', '👍', '👎', '🙏',
  '❤️', '💯', '🔥', '✅', '❌', '🎉', '💪', '🤝',
]

function select(emoji, togglePopover) {
  model.value = emoji
  togglePopover()
}
</script>
