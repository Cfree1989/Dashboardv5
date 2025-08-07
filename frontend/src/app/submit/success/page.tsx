import React from 'react';
import Link from 'next/link';
import { CheckCircle } from 'lucide-react';

export default function SuccessPage({ searchParams }: { searchParams: { job?: string } }) {
  const jobId = searchParams.job;
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-green-50 to-white py-12">
      <div className="bg-card p-8 rounded-xl shadow-md max-w-md w-full text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4 animate-pulse-subtle" />
        <h1 className="text-3xl font-bold text-foreground mb-4">Submission Successful!</h1>
        {jobId ? (
          <p className="text-base text-foreground">Your job ID is <span className="font-mono bg-muted px-1 rounded">{jobId}</span>.</p>
        ) : (
          <p className="text-base text-foreground">Your submission has been received.</p>
        )}
        <p className="mt-6 text-base text-foreground">
          You will receive a confirmation email shortly. Please save your Job ID for tracking.
        </p>
        <div className="mt-8">
          <Link href="/submit">
            <button className="bg-secondary text-secondary-foreground px-4 py-2 rounded-lg btn-transition focus-ring">
              Submit Another Model
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
}