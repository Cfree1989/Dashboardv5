import { useEffect, useState } from 'react';

/**
 * Returns true when the user has enabled Reduced Motion in their OS/browser.
 * Defaults to false during SSR and tests.
 */
export function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !('matchMedia' in window)) return;
    try {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      const update = () => setPrefersReduced(!!mq.matches);
      update();
      mq.addEventListener?.('change', update);
      return () => mq.removeEventListener?.('change', update);
    } catch {
      // no-op
    }
  }, []);

  return prefersReduced;
}


