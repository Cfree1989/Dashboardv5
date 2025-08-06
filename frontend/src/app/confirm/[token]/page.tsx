'use client';

import React, { useEffect, useState } from 'react';

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
    fetch(`/api/v1/confirm/${token}`, {
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

  if (status === 'loading') {
    return <div className="p-8 text-center">Verifying confirmation...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded shadow p-8 max-w-md text-center">
        {status === 'success' && (
          <>
            <h1 className="text-2xl font-bold text-green-600 mb-4">Confirmation Successful!</h1>
            <p>Your job has been confirmed. Thank you!</p>
          </>
        )}
        {status === 'expired' && (
          <>
            <h1 className="text-2xl font-bold text-yellow-600 mb-4">Link Expired</h1>
            <p>{message}</p>
          </>
        )}
        {status === 'error' && (
          <>
            <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
            <p>{message}</p>
          </>
        )}
      </div>
    </div>
  );
}