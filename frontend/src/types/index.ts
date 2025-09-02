// ============================================================================
// CORE BUSINESS TYPES
// ============================================================================

/**
 * Job status enumeration - represents the lifecycle states of a 3D print job
 */
export enum JobStatus {
  UPLOADED = 'UPLOADED',
  PENDING = 'PENDING', 
  READYTOPRINT = 'READYTOPRINT',
  PRINTING = 'PRINTING',
  COMPLETED = 'COMPLETED',
  PAIDPICKEDUP = 'PAIDPICKEDUP',
  REJECTED = 'REJECTED',
  ARCHIVED = 'ARCHIVED'
}

/**
 * Job status action types for status transitions
 */
export type JobStatusAction = 'mark-printing' | 'mark-complete' | 'mark-picked-up';

/**
 * Core Job interface representing a 3D print job
 */
export interface Job {
  id: string;
  short_id?: string;
  display_name?: string;
  student_name?: string;
  student_email?: string;
  original_filename?: string;
  printer?: string;
  color?: string;
  material?: string;
  weight_g?: number;
  time_hours?: number;
  cost_usd?: number;
  created_at?: string;
  notes?: string;
  staff_viewed_at?: string;
  file_path?: string;
  discipline?: string;
  class_number?: string;
  status?: JobStatus;
  payment?: Payment;
  locked_by?: string;
  locked_until?: string;
}

/**
 * Payment information for completed jobs
 */
export interface Payment {
  job_id: string;
  grams: number;
  price_cents: number;
  price_usd: number;
  txn_no: string;
  picked_up_by: string;
  paid_ts: string;
  paid_by_staff: string;
}

/**
 * Staff member information
 */
export interface Staff {
  name: string;
  is_active: boolean;
}

// ============================================================================
// DASHBOARD & UI TYPES
// ============================================================================

/**
 * Job list filters for filtering and searching jobs
 */
export interface JobListFilters {
  status?: JobStatus | string;
  search?: string;
  printer?: string;
  discipline?: string;
}

/**
 * Job card component props
 */
export interface JobCardProps {
  job: Job;
  currentStatus?: JobStatus | string;
  onApprove?: (jobId: string) => void;
  onReject?: (jobId: string) => void;
  onMarkReviewed?: (jobId: string, updatedJob?: Job) => void;
  onStatusAction?: (jobId: string, action: JobStatusAction) => void;
  onUpdate?: (jobId: string, updates: Partial<Job>) => Promise<void>;
  onDelete?: (jobId: string) => Promise<void>;
  onModalOpenChange?: (open: boolean) => void;
  expandSignal?: number;
  collapseSignal?: number;
}

/**
 * Dashboard state management (auth moved to global store)
 */
export interface DashboardState {
  search: {
    value: string;
    debounced: string;
    matchCounts: Record<string, number>;
  };
  refresh: {
    tick: number;
    isRefreshing: boolean;
    pauseRefresh: boolean;
    lastUpdated: string;
  };
  jobOps: {
    isJobOperation: boolean;
    expandSignal: number;
    collapseSignal: number;
  };
  data: {
    status: JobStatus | string;
    counts: Record<string, number>;
  };
}

/**
 * Dashboard action types for useReducer (auth actions removed - managed globally)
 */
export type DashboardAction =
  | { type: 'SET_SEARCH_VALUE'; payload: string }
  | { type: 'SET_DEBOUNCED_SEARCH'; payload: string }
  | { type: 'SET_MATCH_COUNTS'; payload: Record<string, number> }
  | { type: 'INCREMENT_REFRESH_TICK' }
  | { type: 'SET_REFRESHING'; payload: boolean }
  | { type: 'SET_PAUSE_REFRESH'; payload: boolean }
  | { type: 'SET_LAST_UPDATED'; payload: string }
  | { type: 'SET_JOB_OPERATION'; payload: boolean }
  | { type: 'INCREMENT_EXPAND_SIGNAL' }
  | { type: 'INCREMENT_COLLAPSE_SIGNAL' }
  | { type: 'SET_STATUS'; payload: JobStatus | string }
  | { type: 'SET_COUNTS'; payload: Record<string, number> };

/**
 * Job list state management
 */
export interface JobListState {
  data: {
    jobs: Job[];
    hasLoaded: boolean;
  };
  loading: {
    loading: boolean;
    isFetching: boolean;
  };
  error: ErrorState;
  sorting: {
    sortBy: string;
    sortDir: 'asc' | 'desc';
  };
}

// ============================================================================
// ERROR HANDLING TYPES
// ============================================================================

/**
 * Error state for consistent error handling across components
 */
export interface ErrorState {
  hasError: boolean;
  message: string;
  category: string;
  isRetryable: boolean;
  retryCount: number;
  timestamp: Date;
}

/**
 * API error response format
 */
export interface ApiError {
  error: string;
  message: string;
  details?: string;
  code?: string;
  timestamp?: string;
}

// ============================================================================
// MODAL & DIALOG TYPES
// ============================================================================

/**
 * Status change modal configuration
 */
export interface StatusChangeModalConfig {
  action: JobStatusAction;
  title: string;
  description: string;
  confirmVerb: string;
}

/**
 * Review modal state
 */
export interface ReviewModalState {
  reviewed: boolean;
}

/**
 * Confirm dialog configuration
 */
export interface ConfirmDialogConfig {
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  label: string;
  placeholder: string;
  expectedValue: string;
}

// ============================================================================
// MONITORING & HEALTH TYPES
// ============================================================================

/**
 * System metrics for monitoring
 */
export interface SystemMetrics {
  timestamp: string;
  uptime_seconds: number;
  cpu: {
    percent: number;
    count: number;
    frequency_mhz?: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
    used_gb: number;
    percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  process: {
    memory_mb: number;
    cpu_percent: number;
    threads: number;
    open_files: number;
    connections: number;
  };
}

/**
 * Application metrics for monitoring
 */
export interface ApplicationMetrics {
  timestamp: string;
  requests: {
    total: number;
    errors: number;
    error_rate_percent: number;
  };
  performance: {
    slow_endpoints: Array<{
      path: string;
      count: number;
      avg_duration_ms: number;
      error_count: number;
      error_rate: number;
    }>;
    total_endpoints: number;
  };
}

/**
 * Database metrics for monitoring
 */
export interface DatabaseMetrics {
  timestamp: string;
  connectivity: {
    status: string;
    response_time_ms: number;
  };
  tables: {
    jobs: number;
    payments: number;
    events: number;
  };
  recent_activity: {
    jobs_last_24h: number;
    events_last_24h: number;
  };
}

/**
 * Storage metrics for monitoring
 */
export interface StorageMetrics {
  timestamp: string;
  status: string;
  path: string;
  files: {
    count: number;
    directories: number;
    total_size_gb: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent_used: number;
  };
}

/**
 * Redis metrics for monitoring
 */
export interface RedisMetrics {
  timestamp: string;
  rq: {
    queue_size: number;
  };
}

/**
 * Overall health status
 */
export interface HealthStatus {
  status: string;
  timestamp: string;
  uptime_seconds: number;
  health_checks: {
    system: string;
    database: string;
    storage: string;
    redis: string;
  };
  components: {
    system: SystemMetrics;
    application: ApplicationMetrics;
    database: DatabaseMetrics;
    storage: StorageMetrics;
    redis: RedisMetrics;
  };
}

/**
 * Performance alert
 */
export interface PerformanceAlert {
  type: string;
  severity: 'warning' | 'critical' | 'error';
  message: string;
  timestamp: string;
}

// ============================================================================
// CACHE & API TYPES
// ============================================================================

/**
 * Cache entry for API responses
 */
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

/**
 * Pending API request
 */
export interface PendingRequest<T> {
  promise: Promise<T>;
  timestamp: number;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Date range for analytics and filtering
 */
export interface DateRange {
  start: string;
  end: string;
}

/**
 * Date count for analytics
 */
export interface DateCount {
  date: string;
  count: number;
}

/**
 * Generic key-value record
 */
export type Record<K extends string, V> = { [key in K]: V };

// ============================================================================
// TYPE GUARDS & VALIDATORS
// ============================================================================

/**
 * Type guard to check if a value is a valid JobStatus
 */
export function isJobStatus(value: string): value is JobStatus {
  return Object.values(JobStatus).includes(value as JobStatus);
}

/**
 * Type guard to check if a value is a valid JobStatusAction
 */
export function isJobStatusAction(value: string): value is JobStatusAction {
  return ['mark-printing', 'mark-complete', 'mark-picked-up'].includes(value);
}

/**
 * Type guard to check if an object is a valid Job
 */
export function isJob(obj: any): obj is Job {
  return obj && typeof obj.id === 'string';
}

/**
 * Type guard to check if an object is a valid Payment
 */
export function isPayment(obj: any): obj is Payment {
  return obj && typeof obj.job_id === 'string' && typeof obj.price_cents === 'number';
}
