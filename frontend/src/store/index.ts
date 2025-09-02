// Main store index - exports all Zustand stores and utilities

// Export store types
export * from './types';

// Export individual stores (will be created in subsequent steps)
export { useAuthStore } from './slices/auth-store';
export { useDashboardStore } from './slices/dashboard-store';
export { useModalStore } from './slices/modal-store';
export { useJobOperationsStore } from './slices/job-operations-store';

// Export store utilities and hooks
export * from './utils';

// Re-export zustand for convenience
export { create } from 'zustand';
export { subscribeWithSelector } from 'zustand/middleware';
export { devtools } from 'zustand/middleware';
