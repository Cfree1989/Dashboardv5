// Authentication utilities for cookie-based JWT tokens
// This replaces localStorage-based token storage for security

// All API requests now use unified API client instead of individual utilities

export interface AuthUser {
  workstation_id: string;
  isAuthenticated: boolean;
}

export interface LoginResponse {
  message: string;
  workstation_id: string;
}

export interface AuthError {
  message: string;
}

// Get token from client-side cookie (for transition period)
export function getClientToken(): string | null {
  if (typeof window === 'undefined') return null;
  
  // Read from client-side cookie set by backend during transition
  const cookies = document.cookie.split(';');
  const authCookie = cookies.find(cookie => cookie.trim().startsWith('auth_token_client='));
  
  if (authCookie) {
    return authCookie.split('=')[1];
  }
  
  return null;
}

// Check if user is authenticated by attempting to access a protected endpoint
export async function checkAuthStatus(): Promise<AuthUser> {
  try {
    const response = await fetch('/api/v1/auth/protected', {
      method: 'GET',
      credentials: 'include', // Include cookies
    });
    
    if (response.ok) {
      const data = await response.json();
      return {
        workstation_id: data.workstation_id,
        isAuthenticated: true,
      };
    }
  } catch (error) {
    // Silently handle auth check failures
  }
  
  return {
    workstation_id: '',
    isAuthenticated: false,
  };
}

// Login function that handles cookie-based authentication
export async function login(workstationId: string, password: string): Promise<LoginResponse> {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Include cookies in response
    body: JSON.stringify({
      workstation_id: workstationId,
      password: password,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Login failed');
  }

  return data;
}

// Logout function that clears cookies
export async function logout(): Promise<void> {
  try {
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include', // Include cookies
    });
  } catch (error) {
    // Silently handle logout failures
  }
}

// All API requests now use unified API client (frontend/src/lib/unified-api-client.ts)
// Legacy API request functions have been removed

// Legacy support: Get token for components that still expect it  
// TODO: Remove once all remaining usages are updated
export function getLegacyToken(): string | null {
  return getClientToken();
}
