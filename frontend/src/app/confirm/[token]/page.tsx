'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface Props {
  params: {
    token: string;
  };
}

export default function ConfirmPage({ params }: Props) {
  const { token } = params;
  const [status, setStatus] = useState<'loading' | 'success' | 'expired' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`/api/v1/submit/confirm/${token}`, {
      method: 'POST',
    })
      .then(async res => {
        if (res.ok) {
          setStatus('success');
        } else if (res.status === 410) {
          setStatus('expired');
          setMessage('Confirmation link expired. Please request a new link.');
        } else {
          const data = await res.json().catch(() => ({}));
          setStatus('error');
          setMessage(data.message || 'Confirmation failed.');
        }
      })
      .catch(() => {
        setStatus('error');
        setMessage('Network error. Please try again.');
      });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-blue-50 to-white py-12">
      <div className="bg-card p-8 rounded-xl shadow-md max-w-lg w-full text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="animate-spin mx-auto h-12 w-12 text-primary mb-4" />
            <p className="text-base text-muted mb-4">Verifying confirmation...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
            <h1 className="text-3xl font-bold text-foreground mb-4">Job Confirmed!</h1>
            <p className="text-base text-foreground mb-6">Your 3D print job has been successfully confirmed and added to the print queue.</p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h2 className="text-lg font-semibold text-blue-900 mb-2">What Happens Next</h2>
              <div className="text-left text-sm text-blue-800 space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                  <p>Your job is now in the print queue</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                  <p>We'll email you with progress updates</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                  <p>You'll be notified when it's ready for pickup</p>
                </div>
              </div>
            </div>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <p className="text-sm text-green-800">
                <span className="font-medium">✅ Thank you!</span> You can safely close this page. We'll handle everything from here.
              </p>
            </div>
          </>
        )}
        {status === 'expired' && (
          <>
            <AlertTriangle className="mx-auto h-12 w-12 text-yellow-600 mb-4" />
            <h1 className="text-3xl font-bold text-yellow-700 mb-4">Link Expired</h1>
            <p className="text-base text-foreground">{message}</p>
            <div className="mt-8">
              <Link href="/submit">
                <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring">
                  Submit Another Model
                </button>
              </Link>
            </div>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle className="mx-auto h-12 w-12 text-red-600 mb-4" />
            <h1 className="text-3xl font-bold text-red-600 mb-4">Error</h1>
            <p className="text-base text-foreground">{message}</p>
            <div className="mt-8">
              <Link href="/submit">
                <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring">
                  Try Again
                </button>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}