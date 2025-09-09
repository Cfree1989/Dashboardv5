// Dashboard State Store - Zustand store for dashboard state management
// Manages search, refresh, job operations, and data state globally

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { DashboardStore } from '../types';
import { JobStatus } from '../../types';
import { apiClient } from '../../lib/unified-api-client';

export const useDashboardStore = create<DashboardStore>()(
  devtools(
    subscribeWithSelector(
      (set, get) => ({
        // Search state
        searchValue: '',
        debouncedSearch: '',
        matchCounts: {},

        // Refresh state
        refreshTick: 0,
        isRefreshing: false,
        pauseRefresh: false,
        lastUpdated: '',

        // Job operations state
        isJobOperation: false,
        expandSignal: 0,
        collapseSignal: 0,

        // Data state
        currentStatus: JobStatus.UPLOADED,
        counts: {},

        // Sound notification state
        seenUploadedJobIds: new Set<string>(),
        soundBaselineEstablished: false,
        lastUploadedBaselineAt: undefined,

        // Search actions
        setSearchValue: (value: string) => {
          set({ searchValue: value });
        },
        
        setDebouncedSearch: (value: string) => {
          set({ debouncedSearch: value });
        },
        
        setMatchCounts: (counts: Record<string, number>) => {
          set({ matchCounts: counts });
        },

        // Refresh actions
        incrementRefreshTick: () => {
          set((state) => ({ refreshTick: state.refreshTick + 1 }));
        },
        
        setRefreshing: (isRefreshing: boolean) => {
          set({ isRefreshing });
        },
        
        setPauseRefresh: (pause: boolean) => {
          set({ pauseRefresh: pause });
        },
        
        setLastUpdated: (timestamp: string) => {
          set({ lastUpdated: timestamp });
        },

        // Job operations actions
        setJobOperation: (isOperation: boolean) => {
          set({ isJobOperation: isOperation });
        },
        
        incrementExpandSignal: () => {
          set((state) => ({ expandSignal: state.expandSignal + 1 }));
        },
        
        incrementCollapseSignal: () => {
          set((state) => ({ collapseSignal: state.collapseSignal + 1 }));
        },

        // Data actions
        setCurrentStatus: (status: string) => {
          set({ currentStatus: status });
        },
        
        setCounts: (counts: Record<string, number>) => {
          set({ counts });
        },

        // Combined actions
        refreshData: async () => {
          const { setRefreshing, setCounts, setJobOperation, setLastUpdated } = get();
          
          try {
            setRefreshing(true);
            
            const data = await apiClient.request<Record<string, number>>(
              '/api/v1/jobs/counts',
              {},
              { 
                ttl: 30 * 1000, // 30 seconds for counts
                polling: {
                  enabled: true,
                  interval: 45000, // 45 seconds
                  maxInterval: 300000, // 5 minutes max
                  backoffMultiplier: 1.5,
                  activityThreshold: 300000 // 5 minutes
                }
              }
            );
            
            setCounts(data);
            setLastUpdated(new Date().toISOString());
            
            // Reset job operation flag after counts update
            setJobOperation(false);
            
          } catch (error) {
            console.error('Failed to refresh dashboard data:', error);
            // Reset job operation flag even on error
            setJobOperation(false);
          } finally {
            setRefreshing(false);
          }
        },

        // Sound notification actions
        initializeUploadSoundBaseline: (ids: string[], timestamp: string) => {
          set({
            seenUploadedJobIds: new Set<string>(ids),
            soundBaselineEstablished: true,
            lastUploadedBaselineAt: timestamp,
          });
        },
        addSeenUploadedJobIds: (ids: string[]) => {
          set((state) => {
            const merged = new Set<string>(state.seenUploadedJobIds);
            for (const id of ids) merged.add(id);
            return { seenUploadedJobIds: merged } as Partial<DashboardStore>;
          });
        },
        resetUploadSoundState: () => {
          set({
            seenUploadedJobIds: new Set<string>(),
            soundBaselineEstablished: false,
            lastUploadedBaselineAt: undefined,
          });
        },
      })
    ),
    { name: 'dashboard-store' }
  )
);
