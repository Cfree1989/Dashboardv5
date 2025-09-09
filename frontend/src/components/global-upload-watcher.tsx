'use client';

import React, { useEffect, useRef } from 'react';
import { useAuthStore, useDashboardStore, useSoundStore } from '../store';
import { apiClient } from '../lib/unified-api-client';
import { JobStatus } from '../types';
import { initDashboardAudio, playNewUploadSound, configureSound } from '../lib/sound-utils';

export default function GlobalUploadWatcher() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const initializeUploadSoundBaseline = useDashboardStore((s) => s.initializeUploadSoundBaseline);
  const addSeenUploadedJobIds = useDashboardStore((s) => s.addSeenUploadedJobIds);
  const soundBaselineEstablished = useDashboardStore((s) => s.soundBaselineEstablished);
  const seenUploadedJobIds = useDashboardStore((s) => s.seenUploadedJobIds);
  const soundEnabled = useSoundStore((s) => s.soundEnabled);
  const volume = useSoundStore((s) => s.volume);
  const variant = useSoundStore((s) => s.variant);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Global audio initialization on any user interaction
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleUserInteraction = async () => {
      const ok = await initDashboardAudio();
      if (ok) {
        document.removeEventListener('click', handleUserInteraction);
        document.removeEventListener('keydown', handleUserInteraction);
        document.removeEventListener('touchstart', handleUserInteraction);
      }
    };

    // Attempt immediate init (may no-op due to autoplay policy)
    initDashboardAudio();

    document.addEventListener('click', handleUserInteraction);
    document.addEventListener('keydown', handleUserInteraction);
    document.addEventListener('touchstart', handleUserInteraction);

    return () => {
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
    };
  }, [isAuthenticated]);

  // Poll for newly uploaded jobs globally and trigger sound once per new ID
  useEffect(() => {
    if (!isAuthenticated) return;

    const poll = async () => {
      try {
        // Update sound configuration before any potential play
        configureSound({ volume, variant });
        const params = new URLSearchParams();
        params.append('status', JobStatus.UPLOADED);
        params.append('_ts', String(Date.now()));

        const listUrl = `/api/v1/jobs?${params.toString()}`;
        const jobs = await apiClient.request<any[]>(listUrl, { method: 'GET', cache: 'no-store' }, { ttl: 0 });

        const ids: string[] = Array.isArray(jobs) ? jobs.map((j: any) => j?.id).filter(Boolean) : [];

        if (!useDashboardStore.getState().soundBaselineEstablished) {
          initializeUploadSoundBaseline(ids, new Date().toISOString());
          return;
        }

        const currentSeen = useDashboardStore.getState().seenUploadedJobIds;
        const newIds = ids.filter((id) => !currentSeen.has(id));
        if (newIds.length > 0 && soundEnabled) {
          try {
            await playNewUploadSound();
          } catch (e) {
            // ignore play errors to avoid noisy logs
          }
          addSeenUploadedJobIds(newIds);
        }
      } catch (e) {
        // Silent failure; watcher is best-effort
      }
    };

    // Initial poll and interval
    poll();
    intervalRef.current = setInterval(poll, 30000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAuthenticated, initializeUploadSoundBaseline, addSeenUploadedJobIds, soundBaselineEstablished, seenUploadedJobIds, soundEnabled, volume, variant]);

  return null;
}


