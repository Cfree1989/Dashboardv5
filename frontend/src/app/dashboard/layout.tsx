import React, { ReactNode } from 'react';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-gray-800 text-white">
        <div className="p-4 text-xl font-bold">3D Print Dashboard</div>
        <nav>
          <ul>
            <li className="p-2 hover:bg-gray-700">Uploaded</li>
            <li className="p-2 hover:bg-gray-700">Pending</li>
            <li className="p-2 hover:bg-gray-700">Ready to Print</li>
            <li className="p-2 hover:bg-gray-700">Printing</li>
            <li className="p-2 hover:bg-gray-700">Completed</li>
            <li className="p-2 hover:bg-gray-700">Paid & Picked Up</li>
            <li className="p-2 hover:bg-gray-700">Archived</li>
          </ul>
        </nav>
      </aside>
      <main className="flex-1 bg-gray-100 p-8">
        {children}
      </main>
    </div>
  );
}