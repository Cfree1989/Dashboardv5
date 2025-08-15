// Authentication utilities for cookie-based JWT tokens
// This replaces localStorage-based token storage for security

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
    console.error('Auth check failed:', error);
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
    console.error('Logout failed:', error);
  }
}

// API request helper that includes cookies
export async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Include cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (response.status === 401) {
    // Redirect to login on authentication failure
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// Legacy support: Get token for components that still expect it
// This will be removed once all components are updated
export function getLegacyToken(): string | null {
  return getClientToken();
}

// Legacy support: Set token (no-op for cookie-based auth)
// This will be removed once all components are updated
export function setLegacyToken(token: string): void {
  // No-op: tokens are now handled by cookies
  console.warn('setLegacyToken called - tokens are now cookie-based');
}

// Legacy support: Remove token (no-op for cookie-based auth)
// This will be removed once all components are updated
export function removeLegacyToken(): void {
  // No-op: tokens are now handled by cookies
  console.warn('removeLegacyToken called - tokens are now cookie-based');
}
