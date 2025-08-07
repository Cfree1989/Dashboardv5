'use client';

import React from 'react';
import Link from 'next/link';
import { XCircle } from 'lucide-react';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-red-50 to-white">
      <div className="bg-card p-8 rounded-xl shadow-md text-center max-w-md w-full">
        <XCircle className="mx-auto h-12 w-12 text-red-600 mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-4">Something Went Wrong</h1>
        <p className="text-base text-foreground mb-6">
          {error.message || 'An unexpected error occurred.'}
        </p>
        <div className="space-x-4">
          <button
            onClick={() => reset()}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring"
          >
            Try Again
          </button>
          <Link href="/">
            <button className="bg-secondary text-secondary-foreground px-4 py-2 rounded-lg btn-transition focus-ring">
              Go Home
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
}
