// Simplified sound utility functions

/**
 * Tests if audio playback is supported in the current browser
 * @returns True if audio is supported, false otherwise
 */
export function isAudioSupported(): boolean {
  if (typeof window === "undefined") return false

  try {
    const audio = new Audio()
    return typeof audio.play === "function"
  } catch (e) {
    return false
  }
}

/**
 * Plays a notification sound with error handling
 * @param soundUrl The URL of the sound file to play
 * @returns Promise that resolves when the sound starts playing
 */
export async function playNotificationSound(soundUrl = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"): Promise<void> {
  if (typeof window === "undefined") return

  try {
    const audio = new Audio(soundUrl)
    audio.volume = 0.5
    await audio.play()
  } catch (error) {
    console.log("Could not play sound:", error)
    throw error
  }
}
