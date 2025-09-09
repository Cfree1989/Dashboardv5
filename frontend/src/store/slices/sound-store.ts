import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { SoundStore, SoundVariant } from '../types';

export const useSoundStore = create<SoundStore>()(
  devtools(
    persist(
      (set) => ({
        soundEnabled: true,
        volume: 0.3,
        variant: 'chime' as SoundVariant,
        setSoundEnabled: (enabled: boolean) => set({ soundEnabled: enabled }),
        setVolume: (volume: number) => set({ volume: Math.max(0, Math.min(1, volume)) }),
        setVariant: (variant: SoundVariant) => set({ variant }),
      }),
      {
        name: 'sound-config',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({ soundEnabled: state.soundEnabled, volume: state.volume, variant: state.variant }),
      }
    ),
    { name: 'sound-store' }
  )
);


