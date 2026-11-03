import { onMounted, onUnmounted, ref } from 'vue'

export function useMediaQuery(query) {
  const matches = ref(false)
  let mediaQuery = null

  function update() {
    matches.value = mediaQuery?.matches ?? false
  }

  onMounted(() => {
    mediaQuery = window.matchMedia(query)
    update()
    mediaQuery.addEventListener('change', update)
  })

  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', update)
  })

  return matches
}

export function useIsMobile() {
  return useMediaQuery('(max-width: 767px)')
}
