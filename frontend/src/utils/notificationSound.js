const SOUNDS = {
  notification: '/assets/frappe/sounds/email.mp3',
  send: '/assets/frappe/sounds/submit.mp3',
  receive: '/assets/frappe/sounds/alert.mp3',
}

function play(url, volume = 0.3) {
  try {
    const audio = new Audio(url)
    audio.volume = volume
    void audio.play()
  } catch {
    // Browser may block autoplay until user interacts with the page
  }
}

export function playNotificationSound() {
  play(SOUNDS.notification, 0.2)
}

export function playSendSound() {
  play(SOUNDS.send, 0.2)
}

export function playReceiveSound() {
  play(SOUNDS.receive, 0.35)
}
