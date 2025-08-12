/**
 * Sound utilities for dashboard notifications
 * Provides audio feedback for new job uploads and other events
 */

// Audio context for playing sounds
let audioContext: AudioContext | null = null;

/**
 * Initialize the audio context (required for modern browsers)
 */
function initAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
}

/**
 * Play a notification sound for new uploads
 * Uses Web Audio API to generate a pleasant notification tone
 */
export function playNewUploadSound(): void {
  try {
    const ctx = initAudioContext();
    
    // Resume context if suspended (required for autoplay policies)
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    // Create oscillator for the notification tone
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    // Configure the sound
    oscillator.frequency.setValueAtTime(800, ctx.currentTime); // Start at 800Hz
    oscillator.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.1); // Rise to 1200Hz
    
    // Configure volume envelope
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, ctx.currentTime + 0.05); // Fade in
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3); // Fade out
    
    // Start and stop the sound
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.3);
    
  } catch (error) {
    console.warn('Failed to play notification sound:', error);
    // Fallback: try to play a simple beep using HTML5 Audio
    try {
      const audio = new Audio();
      audio.volume = 0.3;
      // Create a simple beep using data URL
      audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
      audio.play().catch(() => {
        // Ignore autoplay policy errors
      });
    } catch (fallbackError) {
      console.warn('Fallback audio also failed:', fallbackError);
    }
  }
}

/**
 * Play a different sound for job status changes
 */
export function playStatusChangeSound(): void {
  try {
    const ctx = initAudioContext();
    
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    // Different frequency pattern for status changes
    oscillator.frequency.setValueAtTime(600, ctx.currentTime);
    oscillator.frequency.linearRampToValueAtTime(800, ctx.currentTime + 0.15);
    
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.2, ctx.currentTime + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.2);
    
  } catch (error) {
    console.warn('Failed to play status change sound:', error);
  }
}

/**
 * Check if audio is supported and enabled
 */
export function isAudioSupported(): boolean {
  return typeof window !== 'undefined' && 
         (window.AudioContext || (window as any).webkitAudioContext) !== undefined;
}

/**
 * Check if user has interacted with the page (required for autoplay)
 */
export function canPlayAudio(): boolean {
  return isAudioSupported() && document.visibilityState === 'visible';
}
