import { computed } from 'vue'

export function useChatbotInstalled() {
  return computed(() => !!window.chatbot_installed)
}
