'use client';
import React, { ReactNode } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const logout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button onClick={logout} className="bg-red-600 text-white px-4 py-2 rounded">
          Logout
        </button>
      </div>
      <div className="max-w-7xl mx-auto">
        {children}
      </div>
    </div>
  );
}