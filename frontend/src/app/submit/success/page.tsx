import React from 'react';
import Link from 'next/link';
import { CheckCircle } from 'lucide-react';

export default function SuccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-green-50 to-white py-12">
      <div className="bg-card p-8 rounded-xl shadow-md max-w-2xl w-full text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4 animate-pulse-subtle" />
        <h1 className="text-3xl font-bold text-foreground mb-4">Model Successfully Uploaded!</h1>
        <p className="text-base text-foreground mb-6">Your 3D model has been successfully uploaded to our system and is now queued for review.</p>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">What to Expect Next</h2>
          <div className="text-left text-sm text-blue-800 space-y-3">
            <div className="flex items-start space-x-2">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-medium">1</span>
              <div>
                <p className="font-medium">Staff Review (1-2 business days)</p>
                <p className="text-blue-700">Our team will examine your model for printability, structural integrity, and compliance with lab guidelines.</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-2">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-medium">2</span>
              <div>
                <p className="font-medium">Email Notification</p>
                <p className="text-blue-700">You'll receive an email with either approval details and pricing, or feedback for required modifications.</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-2">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-medium">3</span>
              <div>
                <p className="font-medium">Confirmation & Payment</p>
                <p className="text-blue-700">If approved, click the email link to confirm final details and add your job to the print queue.</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-2">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-medium">4</span>
              <div>
                <p className="font-medium">Printing & Pickup</p>
                <p className="text-blue-700">Your model will be printed and you'll be notified when it's ready for pickup at the FabLab.</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-yellow-800">
            <span className="font-medium">💡 Tip:</span> Keep an eye on your email (including spam folder) for updates on your submission.
          </p>
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