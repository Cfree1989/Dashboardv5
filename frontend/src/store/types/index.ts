// Store type definitions for Zustand state management

import { JobStatus, Job } from '../../types';
import { AuthUser } from '../../lib/auth';

// Authentication Store Types
export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface AuthActions {
  login: (workstationId: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
  clearError: () => void;
}

export interface AuthStore extends AuthState, AuthActions {}

// Dashboard State Store Types
export interface DashboardState {
  // Search state
  searchValue: string;
  debouncedSearch: string;
  matchCounts: Record<string, number>;
  
  // Refresh state
  refreshTick: number;
  isRefreshing: boolean;
  pauseRefresh: boolean;
  lastUpdated: string;
  
  // Job operations state
  isJobOperation: boolean;
  expandSignal: number;
  collapseSignal: number;
  
  // Data state
  currentStatus: string;
  counts: Record<string, number>;
}

export interface DashboardActions {
  // Search actions
  setSearchValue: (value: string) => void;
  setDebouncedSearch: (value: string) => void;
  setMatchCounts: (counts: Record<string, number>) => void;
  
  // Refresh actions
  incrementRefreshTick: () => void;
  setRefreshing: (isRefreshing: boolean) => void;
  setPauseRefresh: (pause: boolean) => void;
  setLastUpdated: (timestamp: string) => void;
  
  // Job operations actions
  setJobOperation: (isOperation: boolean) => void;
  incrementExpandSignal: () => void;
  incrementCollapseSignal: () => void;
  
  // Data actions
  setCurrentStatus: (status: string) => void;
  setCounts: (counts: Record<string, number>) => void;
  
  // Combined actions
  refreshData: () => Promise<void>;
}

export interface DashboardStore extends DashboardState, DashboardActions {}

// Modal Management Store Types
export type ModalType = 
  | 'review' 
  | 'rejection' 
  | 'approval' 
  | 'statusChange' 
  | 'payment' 
  | 'openFile' 
  | 'deleteConfirm' 
  | 'resend';

export interface ModalConfig {
  type: ModalType;
  props?: any;
  jobId?: string;
}

export interface ModalState {
  activeModals: Map<string, ModalConfig>;
  modalQueue: ModalConfig[];
  preventMultiple: boolean;
}

export interface ModalActions {
  openModal: (modalId: string, config: ModalConfig) => void;
  closeModal: (modalId: string) => void;
  closeAllModals: () => void;
  isModalOpen: (modalId: string) => boolean;
  getModalConfig: (modalId: string) => ModalConfig | undefined;
  queueModal: (config: ModalConfig) => void;
  processModalQueue: () => void;
}

export interface ModalStore extends ModalState, ModalActions {}

// Job Operations Store Types
export interface JobOperationState {
  // Loading states for different operations
  operationLoading: Record<string, boolean>; // jobId -> isLoading
  
  // Operation-specific states
  approvingJobs: Set<string>;
  rejectingJobs: Set<string>;
  reviewingJobs: Set<string>;
  deletingJobs: Set<string>;
  updatingJobs: Set<string>;
  
  // Notes editing state
  editingNotes: Record<string, boolean>; // jobId -> isEditing
  notesDrafts: Record<string, string>; // jobId -> draft content
  savingNotes: Record<string, boolean>; // jobId -> isSaving
  
  // Messages and errors
  messages: Record<string, string>; // jobId -> message
  errors: Record<string, string>; // jobId -> error message
}

export interface JobOperationActions {
  // Operation state management
  setOperationLoading: (jobId: string, operation: string, loading: boolean) => void;
  
  // Job operation actions
  approveJob: (jobId: string) => Promise<void>;
  rejectJob: (jobId: string, reason: string) => Promise<void>;
  markJobReviewed: (jobId: string, reviewed: boolean) => Promise<void>;
  deleteJob: (jobId: string) => Promise<void>;
  updateJob: (jobId: string, updates: Partial<Job>) => Promise<void>;
  
  // Notes management
  startEditingNotes: (jobId: string, currentNotes: string) => void;
  updateNotesDraft: (jobId: string, draft: string) => void;
  saveNotes: (jobId: string, staffName: string) => Promise<void>;
  cancelNotesEditing: (jobId: string) => void;
  
  // Message management
  setMessage: (jobId: string, message: string) => void;
  setError: (jobId: string, error: string) => void;
  clearMessage: (jobId: string) => void;
  clearError: (jobId: string) => void;
  clearJobState: (jobId: string) => void;
}

export interface JobOperationStore extends JobOperationState, JobOperationActions {}

// Combined store types for convenience
export interface StoreState {
  auth: AuthState;
  dashboard: DashboardState;
  modals: ModalState;
  jobOperations: JobOperationState;
}
