import React from 'react';

export default function SuccessPage({ searchParams }: { searchParams: { job?: string } }) {
  const jobId = searchParams.job;
  return (
    <div className="min-h-screen bg-green-50 py-12">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow p-8 text-center">
        <h1 className="text-2xl font-bold text-green-700 mb-4">Submission Successful!</h1>
        {jobId ? (
          <p className="text-gray-800">Your job ID is <span className="font-mono">{jobId}</span>.</p>
        ) : (
          <p className="text-gray-800">Your submission has been received.</p>
        )}
        <p className="mt-6">
          You will receive a confirmation email shortly. Please save your Job ID for tracking.        
        </p>
      </div>
    </div>
  );
}