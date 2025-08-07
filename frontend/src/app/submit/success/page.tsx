import React from 'react';
import Link from 'next/link';
import { CheckCircle } from 'lucide-react';

export default function SuccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-green-50 to-white py-12">
      <div className="bg-card p-8 rounded-xl shadow-md max-w-md w-full text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4 animate-pulse-subtle" />
        <h1 className="text-3xl font-bold text-foreground mb-4">Submission Successful!</h1>
        <p className="text-base text-foreground">Your submission has been received.</p>
        <div className="mt-6 text-left text-sm text-muted-foreground space-y-2">
          <p><span className="font-medium text-foreground">What happens next:</span></p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Staff will review your model and either approve or request changes.</li>
            <li>If approved, you’ll receive an email with a link to confirm the final cost and proceed.</li>
            <li>If rejected, you’ll receive an email stating the issues.</li>
            <li>Once you confirm, your job enters the queue to be printed.</li>
            <li>We’ll notify you when your print is ready for pickup.</li>
          </ol>
        </div>
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