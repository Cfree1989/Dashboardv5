// Modal Management Store - Zustand store for modal state management
// Centralizes modal state for job-card and other components

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { ModalStore, ModalType, ModalConfig } from '../types';

export const useModalStore = create<ModalStore>()(
  devtools(
    (set, get) => ({
      // State
      activeModals: new Map<string, ModalConfig>(),
      modalQueue: [],
      preventMultiple: false,

      // Actions
      openModal: (modalId: string, config: ModalConfig) => {
        const { activeModals, preventMultiple, queueModal } = get();
        
        // If preventMultiple is enabled and other modals are open, queue this modal
        if (preventMultiple && activeModals.size > 0) {
          queueModal(config);
          return;
        }
        
        set((state) => ({
          activeModals: new Map(state.activeModals.set(modalId, config))
        }));
      },

      closeModal: (modalId: string) => {
        set((state) => {
          const newModals = new Map(state.activeModals);
          newModals.delete(modalId);
          return { activeModals: newModals };
        });
        
        // Process queue after closing modal
        setTimeout(() => {
          const { processModalQueue } = get();
          processModalQueue();
        }, 100);
      },

      closeAllModals: () => {
        set({ 
          activeModals: new Map(),
          modalQueue: [] // Clear queue as well
        });
      },

      isModalOpen: (modalId: string) => {
        const { activeModals } = get();
        return activeModals.has(modalId);
      },

      getModalConfig: (modalId: string) => {
        const { activeModals } = get();
        return activeModals.get(modalId);
      },

      queueModal: (config: ModalConfig) => {
        set((state) => ({
          modalQueue: [...state.modalQueue, config]
        }));
      },

      processModalQueue: () => {
        const { modalQueue, activeModals, openModal } = get();
        
        // If no modals are open and there are queued modals, open the next one
        if (activeModals.size === 0 && modalQueue.length > 0) {
          const nextModal = modalQueue[0];
          const modalId = `${nextModal.type}-${nextModal.jobId || 'default'}-${Date.now()}`;
          
          // Remove from queue and open
          set((state) => ({
            modalQueue: state.modalQueue.slice(1)
          }));
          
          openModal(modalId, nextModal);
        }
      },

      // Helper methods for specific modal types
      openReviewModal: (jobId: string, reviewed: boolean) => {
        const modalId = `review-${jobId}`;
        get().openModal(modalId, {
          type: 'review',
          jobId,
          props: { reviewed }
        });
        return modalId;
      },

      openRejectionModal: (jobId: string) => {
        const modalId = `rejection-${jobId}`;
        get().openModal(modalId, {
          type: 'rejection',
          jobId
        });
        return modalId;
      },

      openApprovalModal: (jobId: string, material?: string, currentPrinter?: string) => {
        const modalId = `approval-${jobId}`;
        get().openModal(modalId, {
          type: 'approval',
          jobId,
          props: { material, currentPrinter }
        });
        return modalId;
      },

      openStatusChangeModal: (jobId: string, action: string, title: string, description: string, confirmVerb: string) => {
        const modalId = `statusChange-${jobId}`;
        get().openModal(modalId, {
          type: 'statusChange',
          jobId,
          props: { action, title, description, confirmVerb }
        });
        return modalId;
      },

      openPaymentModal: (jobId: string) => {
        const modalId = `payment-${jobId}`;
        get().openModal(modalId, {
          type: 'payment',
          jobId
        });
        return modalId;
      },

      openFileModal: (jobId: string) => {
        const modalId = `openFile-${jobId}`;
        get().openModal(modalId, {
          type: 'openFile',
          jobId
        });
        return modalId;
      },

      openDeleteConfirmModal: (jobId: string) => {
        const modalId = `deleteConfirm-${jobId}`;
        get().openModal(modalId, {
          type: 'deleteConfirm',
          jobId
        });
        return modalId;
      },

      openResendModal: (jobId: string) => {
        const modalId = `resend-${jobId}`;
        get().openModal(modalId, {
          type: 'resend',
          jobId
        });
        return modalId;
      },

      // Utility methods
      hasActiveModals: () => {
        const { activeModals } = get();
        return activeModals.size > 0;
      },

      getActiveModalIds: () => {
        const { activeModals } = get();
        return Array.from(activeModals.keys());
      },

      getActiveModalsByType: (type: ModalType) => {
        const { activeModals } = get();
        const modals = Array.from(activeModals.entries());
        return modals.filter(([_, config]) => config.type === type);
      },

    }),
    { name: 'modal-store' }
  )
);
