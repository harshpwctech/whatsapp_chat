import './index.css'
import { createApp } from 'vue'
import { initSocket } from './socket'
import App from './App.vue'
import { Button, Badge, setConfig, frappeRequest, FeatherIcon } from 'frappe-ui'

const app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.component('Button', Button)
app.component('Badge', Badge)
app.component('FeatherIcon', FeatherIcon)

async function boot() {
  if (import.meta.env.DEV) {
    const values = await frappeRequest({
      url: '/api/method/whatsapp_chat.www.whatsapp_inbox.get_context_for_dev',
    })
    for (const key in values) {
      window[key] = values[key]
    }
  }

  const socket = initSocket()
  app.config.globalProperties.$socket = socket
  app.provide('socket', socket)
  app.mount('#app')
}

boot()
