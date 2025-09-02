// Authentication Store - Zustand store for global auth state
// Manages authentication state, user info, and auth operations

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { AuthStore } from '../types';
import { login as authLogin, logout as authLogout, checkAuthStatus as authCheck } from '../../lib/auth';

export const useAuthStore = create<AuthStore>()(
  devtools(
    (set, get) => ({
      // State
      user: null,
      isAuthenticated: false,
      loading: true,
      error: null,

      // Actions
      login: async (workstationId: string, password: string) => {
        set({ loading: true, error: null });
        try {
          const response = await authLogin(workstationId, password);
          
          // Create user object from login response
          const user = {
            workstation_id: response.workstation_id,
            isAuthenticated: true,
          };
          
          set({ 
            user,
            isAuthenticated: true,
            loading: false,
            error: null 
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed';
          set({ 
            user: null,
            isAuthenticated: false,
            loading: false,
            error: errorMessage 
          });
          throw error; // Re-throw for component error handling
        }
      },

      logout: async () => {
        set({ loading: true });
        try {
          await authLogout();
          set({ 
            user: null,
            isAuthenticated: false,
            loading: false,
            error: null 
          });
        } catch (error) {
          // Always clear auth state on logout, even if server request fails
          set({ 
            user: null,
            isAuthenticated: false,
            loading: false,
            error: null 
          });
        }
      },

      checkAuthStatus: async () => {
        set({ loading: true });
        try {
          const authUser = await authCheck();
          
          if (authUser.isAuthenticated) {
            set({ 
              user: authUser,
              isAuthenticated: true,
              loading: false,
              error: null 
            });
          } else {
            set({ 
              user: null,
              isAuthenticated: false,
              loading: false,
              error: null 
            });
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Authentication check failed';
          set({ 
            user: null,
            isAuthenticated: false,
            loading: false,
            error: errorMessage 
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    { name: 'auth-store' }
  )
);
