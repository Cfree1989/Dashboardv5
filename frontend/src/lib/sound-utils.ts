/**
 * Sound utilities for dashboard notifications
 * Provides audio feedback for new job uploads and other events
 */

// Audio context for playing sounds
let audioContext: AudioContext | null = null;
let audioReady: boolean = false;
let userInteractionDetected: boolean = false;

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
    
    // Configure the sound - pleasant two-tone notification
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
    audio.volume = 0.3;
    
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
    
    // Generate tone data
    for (let i = 0; i < samples; i++) {
      const t = i / sampleRate;
      const frequency = 800 + (400 * t / duration); // Rising tone from 800Hz to 1200Hz
      const amplitude = Math.sin(2 * Math.PI * frequency * t) * (1 - t / duration) * 0.3; // Fade out
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