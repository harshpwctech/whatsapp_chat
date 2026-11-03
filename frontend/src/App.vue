<template>
  <FrappeUIProvider>
    <Inbox />
  </FrappeUIProvider>
</template>

<script setup>
import { FrappeUIProvider, usePageMeta } from 'frappe-ui'
import Inbox from '@/pages/Inbox.vue'

usePageMeta(() => ({
  title: 'WhatsApp Inbox',
  icon: window.favicon || '/assets/frappe/images/frappe-favicon.svg',
}))
</script>
