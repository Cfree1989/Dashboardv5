/**
 * Sound notification utility for 3D Print Management System
 * Handles audio notifications for various system events
 */

export class SoundNotifications {
  private static instance: SoundNotifications;
  private audioContext: AudioContext | null = null;
  private enabled: boolean = true;

  private constructor() {
    // Check if audio is supported
    this.enabled = typeof window !== 'undefined' && 'Audio' in window;
  }

  public static getInstance(): SoundNotifications {
    if (!SoundNotifications.instance) {
      SoundNotifications.instance = new SoundNotifications();
    }
    return SoundNotifications.instance;
  }

  /**
   * Enable or disable sound notifications
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (typeof window !== 'undefined') {
      localStorage.setItem('sound-notifications-enabled', String(enabled));
    }
  }

  /**
   * Check if sound notifications are enabled
   */
  isEnabled(): boolean {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sound-notifications-enabled');
      return stored !== null ? stored === 'true' : this.enabled;
    }
    return this.enabled;
  }

  /**
   * Play success notification sound for file uploads
   */
  async playUploadSuccess(): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      // Try to play a notification sound
      await this.playNotificationSound(800, 200); // High pitch, short duration
      setTimeout(() => this.playNotificationSound(600, 200), 150); // Lower pitch, slight delay
    } catch (error) {
      console.warn('Could not play upload success sound:', error);
    }
  }

  /**
   * Play error notification sound
   */
  async playError(): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await this.playNotificationSound(300, 500); // Low pitch, longer duration
    } catch (error) {
      console.warn('Could not play error sound:', error);
    }
  }

  /**
   * Play general notification sound
   */
  async playNotification(): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await this.playNotificationSound(650, 200);
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  }

  /**
   * Generate and play a simple tone using Web Audio API
   */
  private async playNotificationSound(frequency: number, duration: number): Promise<void> {
    if (typeof window === 'undefined') return;

    // Request user gesture for audio if needed
    if (!this.audioContext) {
      try {
        // @ts-ignore - AudioContext might not be in older browsers
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      } catch (e) {
        // Fallback to HTML5 audio if Web Audio API fails
        return this.playHTMLAudio();
      }
    }

    // Resume audio context if suspended (required after user gesture)
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    return new Promise((resolve) => {
      if (!this.audioContext) {
        resolve();
        return;
      }

      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';

      // Smooth volume envelope
      const now = this.audioContext.currentTime;
      gainNode.gain.setValueAtTime(0, now);
      gainNode.gain.linearRampToValueAtTime(0.2, now + 0.01); // Quick attack
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration / 1000); // Gradual decay

      oscillator.start(now);
      oscillator.stop(now + duration / 1000);

      oscillator.onended = () => resolve();
    });
  }

  /**
   * Fallback to HTML5 audio with data URI for simple beep
   */
  private playHTMLAudio(): Promise<void> {
    return new Promise((resolve) => {
      try {
        // Create a simple beep sound using data URI
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvWchAjqT2e/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvWc=');
        audio.volume = 0.3;
        audio.play().catch(() => {
          // Silent fail if audio play is blocked
          resolve();
        });
        setTimeout(resolve, 200);
      } catch (error) {
        resolve();
      }
    });
  }

  /**
   * Initialize audio context on user gesture (required by browsers)
   */
  async initializeAudio(): Promise<void> {
    if (typeof window === 'undefined' || this.audioContext) return;

    try {
      // @ts-ignore - AudioContext might not be in older browsers
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }
    } catch (error) {
      console.warn('Could not initialize audio context:', error);
    }
  }
}

// Export singleton instance
export const soundNotifications = SoundNotifications.getInstance();

// Convenience functions
export const playUploadSuccessSound = () => soundNotifications.playUploadSuccess();
export const playErrorSound = () => soundNotifications.playError();
export const playNotificationSound = () => soundNotifications.playNotification();
