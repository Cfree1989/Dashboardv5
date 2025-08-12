/**
 * Tests for sound utilities
 */

import { playNewUploadSound, playStatusChangeSound, isAudioSupported, canPlayAudio } from './sound-utils';

// Mock Web Audio API
const mockOscillator = {
  frequency: {
    setValueAtTime: jest.fn(),
    exponentialRampToValueAtTime: jest.fn(),
    linearRampToValueAtTime: jest.fn(),
  },
  start: jest.fn(),
  stop: jest.fn(),
  connect: jest.fn(),
};

const mockGainNode = {
  gain: {
    setValueAtTime: jest.fn(),
    linearRampToValueAtTime: jest.fn(),
    exponentialRampToValueAtTime: jest.fn(),
  },
  connect: jest.fn(),
};

const mockAudioContext = {
  createOscillator: jest.fn(() => mockOscillator),
  createGain: jest.fn(() => mockGainNode),
  currentTime: 123.456,
  state: 'running',
  resume: jest.fn(),
  destination: {},
};

// Mock HTML5 Audio
const mockAudio = {
  volume: 0,
  src: '',
  play: jest.fn().mockResolvedValue(undefined),
};

// Mock console methods
const originalConsoleWarn = console.warn;
const mockConsoleWarn = jest.fn();

describe('sound-utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    console.warn = mockConsoleWarn;
    
    // Mock global objects
    global.window = {
      AudioContext: jest.fn(() => mockAudioContext),
      webkitAudioContext: jest.fn(() => mockAudioContext),
    } as any;
    
    global.Audio = jest.fn(() => mockAudio) as any;
    global.document = {
      visibilityState: 'visible',
    } as any;
    
    // Reset mock implementations
    mockAudioContext.createOscillator.mockReturnValue(mockOscillator);
    mockAudioContext.createGain.mockReturnValue(mockGainNode);
    mockAudioContext.state = 'running';
  });

  afterEach(() => {
    console.warn = originalConsoleWarn;
  });

  describe('isAudioSupported', () => {
    it('should return true when AudioContext is available', () => {
      expect(isAudioSupported()).toBe(true);
    });

    it('should return true when webkitAudioContext is available', () => {
      delete (global.window as any).AudioContext;
      expect(isAudioSupported()).toBe(true);
    });

    it('should return false when no audio context is available', () => {
      delete (global.window as any).AudioContext;
      delete (global.window as any).webkitAudioContext;
      expect(isAudioSupported()).toBe(false);
    });
  });

  describe('canPlayAudio', () => {
    it('should return true when audio is supported and page is visible', () => {
      expect(canPlayAudio()).toBe(true);
    });

    it('should return false when page is hidden', () => {
      (global.document as any).visibilityState = 'hidden';
      expect(canPlayAudio()).toBe(false);
    });

    it('should return false when audio is not supported', () => {
      delete (global.window as any).AudioContext;
      delete (global.window as any).webkitAudioContext;
      expect(canPlayAudio()).toBe(false);
    });
  });

  describe('playNewUploadSound', () => {
    it('should create and play audio when AudioContext is available', () => {
      playNewUploadSound();

      expect(mockAudioContext.createOscillator).toHaveBeenCalled();
      expect(mockAudioContext.createGain).toHaveBeenCalled();
      expect(mockOscillator.connect).toHaveBeenCalledWith(mockGainNode);
      expect(mockGainNode.connect).toHaveBeenCalledWith(mockAudioContext.destination);
      expect(mockOscillator.start).toHaveBeenCalledWith(mockAudioContext.currentTime);
      expect(mockOscillator.stop).toHaveBeenCalledWith(mockAudioContext.currentTime + 0.3);
    });

    it('should resume suspended audio context', () => {
      mockAudioContext.state = 'suspended';
      
      playNewUploadSound();

      expect(mockAudioContext.resume).toHaveBeenCalled();
    });

    it('should fall back to HTML5 Audio when Web Audio API fails', () => {
      mockAudioContext.createOscillator.mockImplementation(() => {
        throw new Error('AudioContext not supported');
      });

      playNewUploadSound();

      expect(mockAudio.volume).toBe(0.3);
      expect(mockAudio.src).toContain('data:audio/wav;base64');
      expect(mockAudio.play).toHaveBeenCalled();
    });

    it('should handle complete audio failure gracefully', () => {
      mockAudioContext.createOscillator.mockImplementation(() => {
        throw new Error('AudioContext not supported');
      });
      mockAudio.play.mockRejectedValue(new Error('Autoplay blocked'));

      expect(() => playNewUploadSound()).not.toThrow();
      expect(mockConsoleWarn).toHaveBeenCalledWith('Failed to play notification sound:', expect.any(Error));
    });
  });

  describe('playStatusChangeSound', () => {
    it('should create and play status change audio', () => {
      playStatusChangeSound();

      expect(mockAudioContext.createOscillator).toHaveBeenCalled();
      expect(mockAudioContext.createGain).toHaveBeenCalled();
      expect(mockOscillator.start).toHaveBeenCalledWith(mockAudioContext.currentTime);
      expect(mockOscillator.stop).toHaveBeenCalledWith(mockAudioContext.currentTime + 0.2);
    });

    it('should handle audio failure gracefully', () => {
      mockAudioContext.createOscillator.mockImplementation(() => {
        throw new Error('AudioContext not supported');
      });

      expect(() => playStatusChangeSound()).not.toThrow();
      expect(mockConsoleWarn).toHaveBeenCalledWith('Failed to play status change sound:', expect.any(Error));
    });
  });
});
