import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-red-50 to-white">
      <div className="bg-card p-8 rounded-xl shadow-md text-center max-w-md w-full">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-600 mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-4">Page Not Found</h1>
        <p className="text-base text-foreground mb-6">
          Sorry, the page you are looking for does not exist.
        </p>
        <Link href="/">
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring">
            Go Home
          </button>
        </Link>
      </div>
    </div>
  );
}
