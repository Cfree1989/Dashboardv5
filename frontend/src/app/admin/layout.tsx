"use client";
import React, { ReactNode } from 'react';
import { HeaderNav } from '../../components/layout/header-nav';

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <HeaderNav />
      {children}
    </div>
  );
}
