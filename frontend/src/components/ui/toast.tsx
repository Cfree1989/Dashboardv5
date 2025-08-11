"use client";
import React, { createContext, useCallback, useContext, useState } from 'react';

type Toast = { id: number; message: string };

type ToastContextValue = {
  show: (message: string, durationMs?: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback((message: string, durationMs: number = 2000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, durationMs);
  }, []);

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-[1000] space-y-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto bg-gray-900 text-white text-sm px-3 py-2 rounded-lg shadow-lg border border-gray-800"
            role="status"
            aria-live="polite"
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}


