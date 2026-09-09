import React, { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

/**
 * Floating "Back to Top" button — appears after scrolling 300px down the main content.
 * Attaches to the scrollable <main> element via the data attribute approach,
 * falling back to window scroll for broader compatibility.
 */
export default function ScrollToTop({ scrollContainerRef }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = scrollContainerRef?.current ?? window;
    const getScrollTop = () =>
      scrollContainerRef?.current
        ? scrollContainerRef.current.scrollTop
        : window.scrollY;

    const handleScroll = () => setVisible(getScrollTop() > 300);

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [scrollContainerRef]);

  const scrollToTop = () => {
    const el = scrollContainerRef?.current;
    if (el) {
      el.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  if (!visible) return null;

  return (
    <button
      onClick={scrollToTop}
      aria-label="Back to top"
      className="fixed bottom-6 right-6 z-40 p-3 rounded-full bg-slate-800 text-white shadow-lg
                 hover:bg-brand-600 transition-all duration-200 hover:scale-110 cursor-pointer
                 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
      title="Back to top"
    >
      <ArrowUp className="w-5 h-5" />
    </button>
  );
}
