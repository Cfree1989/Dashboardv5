// Dashboard State Store - Zustand store for dashboard state management
// This file will be implemented in Step 3: Create Dashboard State Store

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { DashboardStore } from '../types';
import { JobStatus } from '../../types';

// Placeholder - will be fully implemented in Step 3
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

        // Actions - placeholders
        setSearchValue: (value: string) => {
          set({ searchValue: value });
        },
        setDebouncedSearch: (value: string) => {
          set({ debouncedSearch: value });
        },
        setMatchCounts: (counts: Record<string, number>) => {
          set({ matchCounts: counts });
        },
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
        setJobOperation: (isOperation: boolean) => {
          set({ isJobOperation: isOperation });
        },
        incrementExpandSignal: () => {
          set((state) => ({ expandSignal: state.expandSignal + 1 }));
        },
        incrementCollapseSignal: () => {
          set((state) => ({ collapseSignal: state.collapseSignal + 1 }));
        },
        setCurrentStatus: (status: string) => {
          set({ currentStatus: status });
        },
        setCounts: (counts: Record<string, number>) => {
          set({ counts });
        },
        refreshData: async () => {
          // Implementation coming in Step 3
          console.log('Dashboard store refreshData - to be implemented');
        },
      })
    ),
    { name: 'dashboard-store' }
  )
);
