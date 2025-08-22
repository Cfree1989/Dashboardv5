"use client";
import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, Shield, RefreshCcw, LogOut, BarChart3 } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { logout } from '../../lib/auth';

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

  const onLogout = async () => {
    try {
      await logout();
      if (typeof window !== 'undefined' && window.location) {
        try { window.location.assign('/login'); } catch { window.location.href = '/login'; }
      }
    } catch (error) {
      // Fallback to direct navigation
      if (typeof window !== 'undefined' && window.location) {
        try { window.location.assign('/login'); } catch { window.location.href = '/login'; }
      }
    }
  };

  return (
    <div className="w-full border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Navigation */}
          <div className="flex items-center space-x-8">
            <Link
              href="/dashboard"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === '/dashboard'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
              }`}
            >
              <LayoutDashboard className="h-5 w-5" />
              <span>Dashboard</span>
            </Link>

            <Link
              href="/admin"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname.startsWith('/admin')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
              }`}
            >
              <Shield className="h-5 w-5" />
              <span>Admin</span>
            </Link>

            <Link
              href="/analytics"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname.startsWith('/analytics')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
              }`}
            >
              <BarChart3 className="h-5 w-5" />
              <span>Analytics</span>
            </Link>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center space-x-4">
            {lastUpdated && (
              <div className="text-sm text-gray-500">
                Last updated: {lastUpdated}
              </div>
            )}
            
            <button
              onClick={onRefresh}
              className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 transition-colors"
              title="Refresh page"
            >
              <RefreshCcw className="h-5 w-5" />
              <span className="hidden sm:inline">Refresh</span>
            </button>

            <button
              onClick={onLogout}
              className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-red-700 hover:text-red-800 hover:bg-red-50 transition-colors"
              title="Logout"
            >
              <LogOut className="h-5 w-5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


