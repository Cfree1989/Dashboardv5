// Store utilities and common patterns

import { useCallback, useEffect } from 'react';

// Utility type for store selectors
export type StoreSelector<T, R> = (state: T) => R;

// Utility for creating stable selectors
export function createSelector<T, R>(selector: StoreSelector<T, R>) {
  return selector;
}

// Utility for debounced store updates
export function useDebounce<T>(value: T, delay: number, callback: (value: T) => void) {
  useEffect(() => {
    const timer = setTimeout(() => callback(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay, callback]);
}

// Utility for creating store actions with error handling
export function createStoreAction<T extends any[], R>(
  action: (...args: T) => Promise<R>,
  errorHandler?: (error: Error) => void
) {
  return useCallback(async (...args: T): Promise<R | undefined> => {
    try {
      return await action(...args);
    } catch (error) {
      if (errorHandler) {
        errorHandler(error as Error);
      } else {
        console.error('Store action error:', error);
      }
      return undefined;
    }
  }, [action, errorHandler]);
}

// Utility for store state reset
export function createResetAction<T>(initialState: T) {
  return () => initialState;
}

// Utility for optimistic updates
export interface OptimisticUpdate<T> {
  id: string;
  optimisticState: Partial<T>;
  revertState?: Partial<T>;
}

export function createOptimisticUpdate<T>(
  id: string,
  optimisticState: Partial<T>,
  revertState?: Partial<T>
): OptimisticUpdate<T> {
  return {
    id,
    optimisticState,
    revertState,
  };
}

// Common store patterns
export const storePatterns = {
  // Loading state pattern
  withLoading: <T>(state: T & { loading: boolean }) => ({
    ...state,
    setLoading: (loading: boolean) => ({ ...state, loading }),
  }),

  // Error state pattern
  withError: <T>(state: T & { error: string | null }) => ({
    ...state,
    setError: (error: string | null) => ({ ...state, error }),
    clearError: () => ({ ...state, error: null }),
  }),

  // Async action pattern
  withAsyncAction: <T, Args extends any[], Return>(
    asyncAction: (...args: Args) => Promise<Return>
  ) => {
    return {
      execute: async (
        set: (updater: (state: T) => T) => void,
        get: () => T,
        ...args: Args
      ): Promise<Return | undefined> => {
        try {
          set((state) => ({ ...state, loading: true, error: null } as T));
          const result = await asyncAction(...args);
          set((state) => ({ ...state, loading: false } as T));
          return result;
        } catch (error) {
          set((state) => ({ ...state, loading: false, error: (error as Error).message } as T));
          return undefined;
        }
      },
    };
  },
};

// Store debugging utilities (development only)
export const storeDebug = {
  // Log all store changes
  logChanges: <T>(storeName: string) => (state: T) => {
    if (process.env.NODE_ENV === 'development') {
      console.group(`🏪 Store Update: ${storeName}`);
      console.log('New state:', state);
      console.groupEnd();
    }
    return state;
  },

  // Validate state structure
  validateState: <T>(validator: (state: T) => boolean, errorMessage: string) => (state: T) => {
    if (process.env.NODE_ENV === 'development' && !validator(state)) {
      console.error(`Store validation failed: ${errorMessage}`, state);
    }
    return state;
  },
};
