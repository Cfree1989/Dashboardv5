"use client";
import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, Shield, RefreshCcw, LogOut, BarChart3 } from 'lucide-react';
import { usePathname } from 'next/navigation';

export function HeaderNav() {
  // Always use Next.js router-aware pathname so it updates on client navigations
  const pathname = usePathname() || '';
  const [lastUpdated, setLastUpdated] = React.useState<string | null>(null);

  React.useEffect(() => {
    try {
      const ts = localStorage.getItem('lastUpdated');
      if (ts) setLastUpdated(ts);
    } catch {}
  }, [pathname]);

  const onRefresh = () => {
    try {
      if (typeof window !== 'undefined') {
        window.location.reload();
      }
    } catch {}
  };

  const onLogout = () => {
    try { localStorage.removeItem('token'); } catch {}
    if (typeof window !== 'undefined' && window.location) {
      try { window.location.assign('/login'); } catch { window.location.href = '/login'; }
    }
  };

  return (
    <div className="w-full border-b border-gray-200 bg-white">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="text-2xl font-bold text-gray-900">3D Print Job Dashboard</div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-gray-500">Last updated: {lastUpdated}</span>
          )}
          <Link
            href="/dashboard"
            aria-current={pathname.startsWith('/dashboard') ? 'page' : undefined}
            className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-white transition-colors hover:bg-orange-600 bg-orange-500 ${
              pathname.startsWith('/dashboard') ? 'border-l-8 border-orange-200 pl-2' : ''
            }`}
          >
            <LayoutDashboard size={16} /> Dashboard
          </Link>
          <Link
            href="/admin"
            aria-current={pathname.startsWith('/admin') ? 'page' : undefined}
            className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-white transition-colors hover:bg-purple-600 bg-purple-500 ${
              pathname.startsWith('/admin') ? 'border-l-8 border-purple-200 pl-2' : ''
            }`}
          >
            <Shield size={16} /> Admin
          </Link>
          <Link
            href="/analytics"
            aria-current={pathname.startsWith('/analytics') ? 'page' : undefined}
            className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-white transition-colors hover:bg-green-700 bg-green-600 ${
              pathname.startsWith('/analytics') ? 'border-l-8 border-green-300 pl-2' : ''
            }`}
          >
            <BarChart3 size={16} /> Analytics
          </Link>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
            onClick={onRefresh}
            title="Refresh"
          >
            <RefreshCcw size={16} /> Refresh
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-red-500 px-3 py-2 text-white hover:bg-red-600"
            onClick={onLogout}
            title="Logout"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </div>
    </div>
  );
}


