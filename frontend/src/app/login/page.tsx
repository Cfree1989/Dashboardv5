'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { XCircle, Loader2 } from 'lucide-react';
import LoginCard from '../../components/LoginCard';

export default function LoginPage() {
  const [workstationId, setWorkstationId] = useState('workstation-1');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workstation_id: workstationId, password }),
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('token', data.token);
        router.push('/dashboard');
      } else {
        setError(data.message || 'Login failed');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-blue-50 to-white">
      <LoginCard>
        <form onSubmit={handleSubmit} className="space-y-4 w-full">
          <h1 className="text-2xl font-bold">Staff Login</h1>
          {error && (
            <div role="alert" aria-live="assertive" className="flex items-center space-x-2 bg-destructive-foreground bg-opacity-10 text-destructive px-4 py-2 mb-2 rounded transition-transform transform">
              <XCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          )}
          <div className="space-y-1">
            <label className="block text-sm font-medium">Workstation</label>
            <select
              value={workstationId}
              onChange={(e) => setWorkstationId(e.target.value)}
              className="mt-1 w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground"
              required
            >
              <option value="workstation-1">Workstation 1</option>
              <option value="workstation-2">Workstation 2</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="block text-sm font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex items-center justify-center bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
            Login
          </button>
        </form>
      </LoginCard>
    </div>
  );
}
