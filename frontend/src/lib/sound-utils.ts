/**
 * Sound utilities for dashboard notifications
 * Provides audio feedback for new job uploads and other events
 */

// Audio context for playing sounds
let audioContext: AudioContext | null = null;
let audioReady: boolean = false;
let userInteractionDetected: boolean = false;

// Current volume/variant are provided by the sound store via setters below
let currentVolume: number = 0.3;
let currentVariant: 'chime' | 'beep' | 'bell' | 'tone' | 'ping' | 'double' | 'triad' | 'siren' = 'chime';

export function configureSound({ volume, variant }: { volume?: number; variant?: 'chime' | 'beep' | 'bell' | 'tone' | 'ping' | 'double' | 'triad' | 'siren' }) {
  if (typeof volume === 'number') currentVolume = Math.max(0, Math.min(1, volume));
  if (variant) currentVariant = variant;
}

/**
 * Initialize the audio context (required for modern browsers)
 * Returns the context but doesn't guarantee it's ready to play
 */
function initAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  
  try {
    if (!audioContext) {
      const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        audioContext = new AudioCtx();
      }
    }
    return audioContext;
  } catch (error) {
    console.warn('Failed to create AudioContext:', error);
    return null;
  }
}

/**
 * Attempt to activate the audio context with user interaction
 * Returns a promise that resolves when audio is ready
 */
async function activateAudioContext(): Promise<boolean> {
  const ctx = initAudioContext();
  if (!ctx) return false;
  
  try {
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }
    
    audioReady = (ctx.state === 'running');
    return audioReady;
  } catch (error) {
    console.warn('Failed to activate AudioContext:', error);
    audioReady = false;
    return false;
  }
}

/**
 * Play a notification sound for new uploads
 * Uses Web Audio API to generate a pleasant notification tone
 */
export async function playNewUploadSound(): Promise<void> {
  // First try to activate audio context
  const isReady = await activateAudioContext();
  if (!isReady || !audioContext) {
    await playFallbackSound();
    return;
  }

  try {
    const ctx = audioContext;
    
    // Double-check context state
    if (ctx.state !== 'running') {
      await playFallbackSound();
      return;
    }

    // Create oscillator for the notification tone
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    // Configure the sound based on variant
    const start = ctx.currentTime;
    switch (currentVariant) {
      case 'beep':
        oscillator.type = 'square';
        oscillator.frequency.setValueAtTime(1000, start);
        break;
      case 'bell':
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(600, start);
        oscillator.frequency.exponentialRampToValueAtTime(1200, start + 0.12);
        break;
      case 'tone':
        oscillator.type = 'triangle';
        oscillator.frequency.setValueAtTime(900, start);
        oscillator.frequency.linearRampToValueAtTime(900, start + 0.2);
        break;
      case 'ping':
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(1200, start);
        break;
      case 'double':
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(900, start);
        // Schedule quick second blip via separate oscillator
        setTimeout(() => {
          try {
            const o2 = ctx.createOscillator();
            const g2 = ctx.createGain();
            o2.type = 'sine';
            o2.frequency.setValueAtTime(1100, ctx.currentTime);
            g2.gain.setValueAtTime(0, ctx.currentTime);
            g2.gain.linearRampToValueAtTime(Math.max(0.0, Math.min(1.0, currentVolume)) * 0.8, ctx.currentTime + 0.02);
            g2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.18);
            o2.connect(g2); g2.connect(ctx.destination);
            o2.start(ctx.currentTime + 0.12);
            o2.stop(ctx.currentTime + 0.3);
          } catch {}
        }, 0);
        break;
      case 'triad':
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(660, start);
        // Add quick stacked tones
        setTimeout(() => {
          try {
            const freqs = [660, 880, 1100];
            freqs.forEach((f, i) => {
              const o = ctx.createOscillator();
              const g = ctx.createGain();
              o.type = 'sine';
              o.frequency.setValueAtTime(f, ctx.currentTime);
              g.gain.setValueAtTime(0, ctx.currentTime);
              g.gain.linearRampToValueAtTime(Math.max(0.0, Math.min(1.0, currentVolume)) * 0.5, ctx.currentTime + 0.02);
              g.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
              o.connect(g); g.connect(ctx.destination);
              o.start(ctx.currentTime + 0.03 * i);
              o.stop(ctx.currentTime + 0.23 + 0.03 * i);
            });
          } catch {}
        }, 0);
        break;
      case 'siren':
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(700, start);
        oscillator.frequency.linearRampToValueAtTime(1200, start + 0.15);
        oscillator.frequency.linearRampToValueAtTime(700, start + 0.3);
        break;
      case 'chime':
      default:
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, start);
        oscillator.frequency.exponentialRampToValueAtTime(1200, start + 0.1);
        break;
    }

    // Configure volume envelope using currentVolume
    const peak = Math.max(0.0, Math.min(1.0, currentVolume));
    gainNode.gain.setValueAtTime(0, start);
    gainNode.gain.linearRampToValueAtTime(peak, start + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.01, start + 0.3);
    
    // Start and stop the sound
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.3);
    
  } catch (error) {
    console.warn('Web Audio API failed, trying fallback:', error);
    await playFallbackSound();
  }
}

/**
 * Fallback sound using HTML5 Audio API
 */
async function playFallbackSound(): Promise<void> {
  try {
    const audio = new Audio();
    audio.volume = Math.max(0.0, Math.min(1.0, currentVolume));
    
    // Create a simple beep sound using data URL (short beep tone)
    const sampleRate = 8000;
    const duration = 0.3;
    const samples = sampleRate * duration;
    const buffer = new ArrayBuffer(44 + samples * 2);
    const view = new DataView(buffer);
    
    // WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, buffer.byteLength - 8, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true); // fmt chunk size
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, 1, true); // mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); // byte rate
    view.setUint16(32, 2, true); // block align
    view.setUint16(34, 16, true); // bits per sample
    writeString(36, 'data');
    view.setUint32(40, samples * 2, true);
    
    // Generate tone data (variant approximations)
    for (let i = 0; i < samples; i++) {
      const t = i / sampleRate;
      let frequency = 800 + (400 * t / duration);
      switch (currentVariant) {
        case 'beep':
          frequency = 1000;
          break;
        case 'bell':
          frequency = 600 + (600 * t / duration);
          break;
        case 'tone':
          frequency = 900;
          break;
        case 'ping':
          frequency = 1200;
          break;
        case 'double':
          frequency = t < duration / 2 ? 900 : 1100;
          break;
        case 'triad':
          frequency = [660, 880, 1100][Math.floor((t / duration) * 3)] || 660;
          break;
        case 'siren':
          frequency = 700 + 500 * Math.abs(Math.sin(2 * Math.PI * (t / duration)));
          break;
        case 'chime':
        default:
          frequency = 800 + (400 * t / duration);
          break;
      }
      const amplitude = Math.sin(2 * Math.PI * frequency * t) * (1 - t / duration) * currentVolume;
      const sample = Math.max(-1, Math.min(1, amplitude));
      view.setInt16(44 + i * 2, sample * 32767, true);
    }
    
    const blob = new Blob([buffer], { type: 'audio/wav' });
    audio.src = URL.createObjectURL(blob);
    
    await audio.play();
    
    // Clean up the blob URL
    setTimeout(() => URL.revokeObjectURL(audio.src), 1000);
    
  } catch (error) {
    console.warn('HTML5 Audio fallback also failed:', error);
  }
}

/**
 * Play a different sound for job status changes
 */
export async function playStatusChangeSound(): Promise<void> {
  const isReady = await activateAudioContext();
  if (!isReady || !audioContext) {
    return;
  }

  try {
    const ctx = audioContext;
    
    if (ctx.state !== 'running') {
      return;
    }

    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    // Different frequency pattern for status changes - gentle chime
    oscillator.frequency.setValueAtTime(600, ctx.currentTime);
    oscillator.frequency.linearRampToValueAtTime(800, ctx.currentTime + 0.15);
    
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.2, ctx.currentTime + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.2);
    
  } catch (error) {
    console.warn('Status change sound failed:', error);
  }
}

/**
 * Check if audio is supported by the browser
 */
export function isAudioSupported(): boolean {
  if (typeof window === 'undefined') return false;
  const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
  return typeof AudioCtx === 'function';
}

/**
 * Check if audio context is ready to play sounds
 */
export function isAudioReady(): boolean {
  return audioReady && audioContext?.state === 'running';
}

/**
 * Check if user has interacted with the page (basic visibility check)
 */
export function canPlayAudio(): boolean {
  return isAudioSupported() && document.visibilityState === 'visible';
}

/**
 * Initialize audio context for dashboard - call this on user interaction
 * Now properly handles async activation and returns status
 */
export async function initDashboardAudio(): Promise<boolean> {
  if (!isAudioSupported()) {
    return false;
  }
  
  try {
    const success = await activateAudioContext();
    if (success) {
      userInteractionDetected = true;
    }
    return success;
  } catch (error) {
    console.warn('Could not initialize dashboard audio:', error);
    return false;
  }
}

/**
 * Test function to manually trigger a sound (useful for debugging)
 * Can be called from browser console as window.testDashboardSound()
 */
export async function testSound(): Promise<void> {
  if (!isAudioSupported()) {
    console.log('Audio is not supported by this browser');
    return;
  }
  
  if (!userInteractionDetected) {
    console.log('User interaction required. Click anywhere on the page first, then try again.');
    return;
  }
  
  await playNewUploadSound();
}

/**
 * Simulate a job count increase to test automatic sound notifications
 * This bypasses the actual API and directly triggers the sound logic
 */
export async function simulateJobIncrease(): Promise<void> {
  if (!isAudioSupported()) {
    console.log('Audio is not supported by this browser');
    return;
  }
  
  if (!userInteractionDetected) {
    console.log('User interaction required. Click anywhere on the page first, then try again.');
    return;
  }
  
  await playNewUploadSound();
}

// Make test functions available globally for easy debugging
if (typeof window !== 'undefined') {
  (window as any).testDashboardSound = testSound;
  (window as any).simulateJobSound = simulateJobIncrease;
}