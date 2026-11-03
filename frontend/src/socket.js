import { io } from 'socket.io-client'

export function initSocket() {
  const host = window.location.hostname
  const siteName = window.site_name
  // Use explicit socketio port only in local dev (URL has a port); production uses same-origin HTTPS
  const port =
    window.location.port && window.socketio_port
      ? `:${window.socketio_port}`
      : ''
  const protocol = port ? 'http' : 'https'
  const url = `${protocol}://${host}${port}/${siteName}`

  return io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  })
}
