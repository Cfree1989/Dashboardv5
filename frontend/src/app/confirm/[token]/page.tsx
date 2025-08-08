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
      <div className="bg-card p-8 rounded-xl shadow-md max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="animate-spin mx-auto h-12 w-12 text-primary mb-4" />
            <p className="text-base text-muted mb-4">Verifying confirmation...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
            <h1 className="text-3xl font-bold text-foreground mb-4">Confirmation Successful!</h1>
            <p className="text-base text-foreground">Your job has been confirmed. Thank you!</p>
            <div className="mt-8">
              <Link href="/dashboard">
                <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring">
                  Back to Dashboard
                </button>
              </Link>
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