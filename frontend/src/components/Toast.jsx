import { useEffect, useRef, useState } from 'react';

export function Toast({ message, onDone, duration = 5000 }) {
  const [visible, setVisible] = useState(Boolean(message));
  const hideTimer = useRef(null);
  const cleanupTimer = useRef(null);

  // When the message changes, show and start a fresh timer
  useEffect(() => {
    // If no message, unmount immediately
    if (!message) {
      setVisible(false);
      return;
    }

    // Show toast
    setVisible(true);

    // Clear any previous timers
    clearTimeout(hideTimer.current);
    clearTimeout(cleanupTimer.current);

    // Schedule hide
    hideTimer.current = setTimeout(() => {
      setVisible(false);
    }, duration);

    return () => {
      clearTimeout(hideTimer.current);
      clearTimeout(cleanupTimer.current);
    };
  }, [message, duration]);

  // After the hide animation completes, call onDone (to clear message)
  useEffect(() => {
    if (!visible && message) {
      // Match CSS transition duration (250ms)
      cleanupTimer.current = setTimeout(() => {
        onDone?.();
      }, 260);
    }
    return () => clearTimeout(cleanupTimer.current);
  }, [visible, message, onDone]);

  if (!message) return null;

  return (
    <div className="toast-wrapper" role="status" aria-live="polite">
      <div className={`toast ${visible ? 'show' : 'hide'}`}>
        {message}
      </div>
    </div>
  );
}

export default Toast;
