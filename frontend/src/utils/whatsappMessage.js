import dayjs from 'dayjs'

export function escapeHtml(text) {
  if (!text) return ''
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function formatWhatsAppMessage(message) {
  if (!message) return ''
  let text = escapeHtml(message)
  text = text.replace(/_(.*?)_/g, '<i>$1</i>')
  text = text.replace(/\*(.*?)\*/g, '<b>$1</b>')
  text = text.replace(/~(.*?)~/g, '<s>$1</s>')
  text = text.replace(/```(.*?)```/g, '<code>$1</code>')
  text = text.replace(/`(.*?)`/g, '<code>$1</code>')
  text = text.replace(/^&gt; (.*)$/gm, '<blockquote>$1</blockquote>')
  text = text.replace(/\n/g, '<br>')
  return text
}

export function parseButtons(buttons) {
  if (!buttons) return []
  if (Array.isArray(buttons)) return buttons
  try {
    return JSON.parse(buttons)
  } catch {
    return []
  }
}

function parseDate(dt) {
  if (!dt) return null
  const parsed = dayjs(dt)
  return parsed.isValid() ? parsed : null
}

export function formatMessageDate(dt) {
  const parsed = parseDate(dt)
  return parsed ? parsed.format('MMM D, YYYY') : ''
}

export function formatMessageTime(dt) {
  const parsed = parseDate(dt)
  return parsed ? parsed.format('hh:mm A') : ''
}

export function formatMessageDateTime(dt) {
  const parsed = parseDate(dt)
  return parsed ? parsed.format('ddd, MMM D, YYYY hh:mm A') : ''
}

export function messageDateKey(dt) {
  const parsed = parseDate(dt)
  return parsed ? parsed.format('MMM D, YYYY') : ''
}

export function formatPrettyDate(dt) {
  const parsed = parseDate(dt)
  if (!parsed) return ''
  const now = dayjs()
  if (parsed.isSame(now, 'day')) return parsed.format('hh:mm A')
  if (parsed.isSame(now.subtract(1, 'day'), 'day')) return 'Yesterday'
  if (parsed.isAfter(now.subtract(7, 'day'))) return parsed.format('ddd')
  return parsed.format('MMM D')
}

export function isHeaderImage(message) {
  const type = (message?.header_type || '').toUpperCase()
  if (type === 'IMAGE') return true
  const media = message?.header_media || ''
  return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(media)
}

export function isHeaderDocument(message) {
  const type = (message?.header_type || '').toUpperCase()
  if (type === 'DOCUMENT') return true
  const media = message?.header_media || ''
  return media && !isHeaderImage(message)
}

export function isContactMessage(message) {
  const text = message?.message || ''
  return text.startsWith('Name:') && text.includes('Phones:')
}

export function parseContactMessage(message) {
  const text = message?.message || ''
  const nameMatch = text.match(/^Name:\s*(.+?),\s*Phones:/)
  const phonesMatch = text.match(/Phones:\s*(.+)$/)
  return {
    name: nameMatch?.[1]?.trim() || '',
    phones: phonesMatch?.[1]?.trim() || '',
  }
}

export function normalizeStatus(status) {
  if (!status) return ''
  return String(status).toLowerCase()
}

export function isDeliveredStatus(status) {
  const s = normalizeStatus(status)
  return ['delivered', 'read', 'marked as read'].includes(s)
}

export function isReadStatus(status) {
  const s = normalizeStatus(status)
  return s === 'read'
}

export function isSentStatus(status) {
  const s = normalizeStatus(status)
  return ['sent', 'success', 'queued'].includes(s)
}

export function isFailedStatus(status) {
  return normalizeStatus(status) === 'failed'
}
