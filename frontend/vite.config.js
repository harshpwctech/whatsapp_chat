import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

function jinjaFavicon() {
  return {
    name: 'whatsapp-inbox-jinja-favicon',
    transformIndexHtml(html, context) {
      if (!context.server) {
        return html.replace(
          /<link rel="icon" href="[^"]*" \/>/,
          '<link rel="icon" href="{{ boot.favicon }}" />',
        )
      }
      return html
    },
  }
}

export default defineConfig(async ({ mode }) => {
  const config = {
    plugins: [
      vue(),
      jinjaFavicon(),
      VitePWA({
        registerType: 'autoUpdate',
        manifest: {
          display: 'standalone',
          name: 'WhatsApp Inbox',
          short_name: 'WhatsApp',
          start_url: '/whatsapp-inbox',
          description: 'WhatsApp conversation inbox',
          icons: [
            {
              src: '/assets/whatsapp_chat/manifest/icon.svg',
              sizes: 'any',
              type: 'image/svg+xml',
              purpose: 'any',
            },
          ],
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      fs: {
        allow: [path.resolve(__dirname, '..')],
      },
    },
    build: {
      outDir: '../whatsapp_chat/public/frontend',
      emptyOutDir: true,
      sourcemap: false,
    },
  }

  const { default: frappeui } = await import('frappe-ui/vite')
  config.plugins.unshift(
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        indexHtmlPath: '../whatsapp_chat/www/whatsapp_inbox.html',
        emptyOutDir: true,
        sourcemap: false,
      },
    }),
  )

  return config
})
