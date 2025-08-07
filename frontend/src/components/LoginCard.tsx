import React from 'react';

interface LoginCardProps {
  children: React.ReactNode;
}

export default function LoginCard({ children }: LoginCardProps) {
  return (
    <div className="bg-card p-8 rounded-xl shadow-md max-w-sm w-full">
      {children}
    </div>
  );
}
