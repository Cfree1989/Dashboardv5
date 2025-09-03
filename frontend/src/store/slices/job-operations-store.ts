// Job Operations Store - Zustand store for job-related operations and state
// Centralizes loading states, operation tracking, and notes management

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { JobOperationStore } from '../types';
import { Job } from '../../types';
import { apiClient } from '../../lib/unified-api-client';

export const useJobOperationsStore = create<JobOperationStore>()(
  devtools(
    (set, get) => ({
      // State
      operationLoading: {},
      approvingJobs: new Set(),
      rejectingJobs: new Set(),
      reviewingJobs: new Set(),
      deletingJobs: new Set(),
      updatingJobs: new Set(),
      editingNotes: {},
      notesDrafts: {},
      savingNotes: {},
      messages: {},
      errors: {},

      // Operation loading management
      setOperationLoading: (jobId: string, operation: string, loading: boolean) => {
        set((state) => ({
          operationLoading: {
            ...state.operationLoading,
            [`${jobId}-${operation}`]: loading
          }
        }));
      },

      // Job operations
      approveJob: async (jobId: string) => {
        const { setOperationLoading, setMessage, setError, clearError } = get();
        
        try {
          setOperationLoading(jobId, 'approve', true);
          clearError(jobId);
          
          set((state) => ({
            approvingJobs: new Set([...Array.from(state.approvingJobs), jobId])
          }));

          await apiClient.post(`/api/v1/jobs/${jobId}/approve`);
          
          setMessage(jobId, 'Job approved successfully');
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to approve job';
          setError(jobId, errorMessage);
          throw error;
        } finally {
          setOperationLoading(jobId, 'approve', false);
          set((state) => {
            const newSet = new Set(state.approvingJobs);
            newSet.delete(jobId);
            return { approvingJobs: newSet };
          });
        }
      },

      rejectJob: async (jobId: string, reason: string) => {
        const { setOperationLoading, setMessage, setError, clearError } = get();
        
        try {
          setOperationLoading(jobId, 'reject', true);
          clearError(jobId);
          
          set((state) => ({
            rejectingJobs: new Set([...Array.from(state.rejectingJobs), jobId])
          }));

          await apiClient.post(`/api/v1/jobs/${jobId}/reject`, { reason });
          
          setMessage(jobId, 'Job rejected successfully');
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to reject job';
          setError(jobId, errorMessage);
          throw error;
        } finally {
          setOperationLoading(jobId, 'reject', false);
          set((state) => {
            const newSet = new Set(state.rejectingJobs);
            newSet.delete(jobId);
            return { rejectingJobs: newSet };
          });
        }
      },

      markJobReviewed: async (jobId: string, reviewed: boolean) => {
        const { setOperationLoading, setMessage, setError, clearError } = get();
        
        try {
          setOperationLoading(jobId, 'review', true);
          clearError(jobId);
          
          set((state) => ({
            reviewingJobs: new Set([...Array.from(state.reviewingJobs), jobId])
          }));

          await apiClient.post(`/api/v1/jobs/${jobId}/review`, { reviewed });
          
          setMessage(jobId, `Job marked as ${reviewed ? 'reviewed' : 'unreviewed'}`);
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to update review status';
          setError(jobId, errorMessage);
          throw error;
        } finally {
          setOperationLoading(jobId, 'review', false);
          set((state) => {
            const newSet = new Set(state.reviewingJobs);
            newSet.delete(jobId);
            return { reviewingJobs: newSet };
          });
        }
      },

      deleteJob: async (jobId: string) => {
        const { setOperationLoading, setMessage, setError, clearError } = get();
        
        try {
          setOperationLoading(jobId, 'delete', true);
          clearError(jobId);
          
          set((state) => ({
            deletingJobs: new Set([...Array.from(state.deletingJobs), jobId])
          }));

          await apiClient.delete(`/api/v1/jobs/${jobId}`);
          
          setMessage(jobId, 'Job deleted successfully');
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to delete job';
          setError(jobId, errorMessage);
          throw error;
        } finally {
          setOperationLoading(jobId, 'delete', false);
          set((state) => {
            const newSet = new Set(state.deletingJobs);
            newSet.delete(jobId);
            return { deletingJobs: newSet };
          });
        }
      },

      updateJob: async (jobId: string, updates: Partial<Job>) => {
        const { setOperationLoading, setMessage, setError, clearError } = get();
        
        try {
          setOperationLoading(jobId, 'update', true);
          clearError(jobId);
          
          set((state) => ({
            updatingJobs: new Set([...Array.from(state.updatingJobs), jobId])
          }));

          await apiClient.put(`/api/v1/jobs/${jobId}`, updates);
          
          setMessage(jobId, 'Job updated successfully');
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to update job';
          setError(jobId, errorMessage);
          throw error;
        } finally {
          setOperationLoading(jobId, 'update', false);
          set((state) => {
            const newSet = new Set(state.updatingJobs);
            newSet.delete(jobId);
            return { updatingJobs: newSet };
          });
        }
      },

      // Notes management
      startEditingNotes: (jobId: string, currentNotes: string) => {
        set((state) => ({
          editingNotes: { ...state.editingNotes, [jobId]: true },
          notesDrafts: { ...state.notesDrafts, [jobId]: currentNotes }
        }));
      },

      updateNotesDraft: (jobId: string, draft: string) => {
        set((state) => ({
          notesDrafts: { ...state.notesDrafts, [jobId]: draft }
        }));
      },

      saveNotes: async (jobId: string, staffName: string) => {
        const { notesDrafts, setMessage, setError, clearError } = get();
        const draft = notesDrafts[jobId] || '';
        
        try {
          set((state) => ({
            savingNotes: { ...state.savingNotes, [jobId]: true }
          }));
          clearError(jobId);

          await apiClient.post(`/api/v1/jobs/${jobId}/notes`, {
            notes: draft,
            staff_name: staffName
          });

          set((state) => ({
            editingNotes: { ...state.editingNotes, [jobId]: false },
            notesDrafts: { ...state.notesDrafts, [jobId]: '' }
          }));
          
          setMessage(jobId, 'Notes saved successfully');
          
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to save notes';
          setError(jobId, errorMessage);
          throw error;
        } finally {
          set((state) => {
            const newSaving = { ...state.savingNotes };
            delete newSaving[jobId];
            return { savingNotes: newSaving };
          });
        }
      },

      cancelNotesEditing: (jobId: string) => {
        set((state) => {
          const newEditing = { ...state.editingNotes };
          const newDrafts = { ...state.notesDrafts };
          delete newEditing[jobId];
          delete newDrafts[jobId];
          return {
            editingNotes: newEditing,
            notesDrafts: newDrafts
          };
        });
      },

      // Message and error management
      setMessage: (jobId: string, message: string) => {
        set((state) => ({
          messages: { ...state.messages, [jobId]: message },
        }));
      },

      setError: (jobId: string, error: string) => {
        set((state) => ({
          errors: { ...state.errors, [jobId]: error },
        }));
      },

      clearMessage: (jobId: string) => {
        set((state) => {
          const newMessages = { ...state.messages };
          delete newMessages[jobId];
          return { messages: newMessages };
        });
      },

      clearError: (jobId: string) => {
        set((state) => {
          const newErrors = { ...state.errors };
          delete newErrors[jobId];
          return { errors: newErrors };
        });
      },

      clearJobState: (jobId: string) => {
        set((state) => {
          // Remove all state for this job
          const newOperationLoading = { ...state.operationLoading };
          const newEditingNotes = { ...state.editingNotes };
          const newNotesDrafts = { ...state.notesDrafts };
          const newSavingNotes = { ...state.savingNotes };
          const newMessages = { ...state.messages };
          const newErrors = { ...state.errors };

          // Remove all operation loading states for this job
          Object.keys(newOperationLoading).forEach(key => {
            if (key.startsWith(`${jobId}-`)) {
              delete newOperationLoading[key];
            }
          });

          delete newEditingNotes[jobId];
          delete newNotesDrafts[jobId];
          delete newSavingNotes[jobId];
          delete newMessages[jobId];
          delete newErrors[jobId];

          // Remove from all job sets
          const newApprovingJobs = new Set(state.approvingJobs);
          const newRejectingJobs = new Set(state.rejectingJobs);
          const newReviewingJobs = new Set(state.reviewingJobs);
          const newDeletingJobs = new Set(state.deletingJobs);
          const newUpdatingJobs = new Set(state.updatingJobs);

          newApprovingJobs.delete(jobId);
          newRejectingJobs.delete(jobId);
          newReviewingJobs.delete(jobId);
          newDeletingJobs.delete(jobId);
          newUpdatingJobs.delete(jobId);

          return {
            operationLoading: newOperationLoading,
            approvingJobs: newApprovingJobs,
            rejectingJobs: newRejectingJobs,
            reviewingJobs: newReviewingJobs,
            deletingJobs: newDeletingJobs,
            updatingJobs: newUpdatingJobs,
            editingNotes: newEditingNotes,
            notesDrafts: newNotesDrafts,
            savingNotes: newSavingNotes,
            messages: newMessages,
            errors: newErrors
          };
        });
      },

      // Utility getters
      isJobLoading: (jobId: string, operation?: string) => {
        const { operationLoading } = get();
        if (operation) {
          return operationLoading[`${jobId}-${operation}`] || false;
        }
        return Object.keys(operationLoading).some(key => 
          key.startsWith(`${jobId}-`) && operationLoading[key]
        );
      },

      getJobMessage: (jobId: string) => {
        const { messages } = get();
        return messages[jobId];
      },

      getJobError: (jobId: string) => {
        const { errors } = get();
        return errors[jobId];
      },

      isEditingNotes: (jobId: string) => {
        const { editingNotes } = get();
        return editingNotes[jobId] || false;
      },

      getNotesDraft: (jobId: string) => {
        const { notesDrafts } = get();
        return notesDrafts[jobId] || '';
      },

      isSavingNotes: (jobId: string) => {
        const { savingNotes } = get();
        return savingNotes[jobId] || false;
      },

    }),
    { name: 'job-operations-store' }
  )
);
