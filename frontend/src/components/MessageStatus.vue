<template>
  <span v-if="isFailedStatus(status)" class="inline-flex items-center">
    <FeatherIcon name="alert-circle" class="h-3.5 w-3.5 text-red-500" />
  </span>
  <CheckIcon
    v-else-if="isSentStatus(status)"
    class="text-ink-gray-5"
  />
  <DoubleCheckIcon
    v-else-if="isDeliveredStatus(status)"
    :class="{ 'text-blue-500': isReadStatus(status) }"
  />
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'
import CheckIcon from '@/components/icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/icons/DoubleCheckIcon.vue'
import {
  isDeliveredStatus,
  isFailedStatus,
  isReadStatus,
  isSentStatus,
} from '@/utils/whatsappMessage.js'

defineProps({
  status: { type: String, default: '' },
})
</script>
