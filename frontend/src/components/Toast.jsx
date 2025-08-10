import React, { useCallback, useEffect, useRef, useState } from "react";

// --- Icons (recreated as inline SVG to avoid new dependencies) ---
const CircleCheckIcon = ({ className, size = 16 }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="12" cy="12" r="10" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const XIcon = ({ className, size = 16 }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </svg>
);


// --- Timer Hook (adapted from your example) ---
function useProgressTimer({ duration, interval = 100, onComplete }) {
  const [progress, setProgress] = useState(duration);
  const timerRef = useRef(0);
  const timerState = useRef({
    startTime: 0,
    remaining: duration,
    isPaused: false,
  });

  const cleanup = useCallback(() => {
    window.clearInterval(timerRef.current);
  }, []);

  const reset = useCallback(() => {
    cleanup();
    setProgress(duration);
    timerState.current = {
      startTime: 0,
      remaining: duration,
      isPaused: false,
    };
  }, [duration, cleanup]);

  const start = useCallback(() => {
    const state = timerState.current;
    state.startTime = Date.now();
    state.isPaused = false;

    timerRef.current = window.setInterval(() => {
      const elapsedTime = Date.now() - state.startTime;
      const remaining = Math.max(0, state.remaining - elapsedTime);
      setProgress(remaining);
      if (remaining <= 0) {
        cleanup();
        onComplete?.();
      }
    }, interval);
  }, [interval, cleanup, onComplete]);

  const pause = useCallback(() => {
    const state = timerState.current;
    if (!state.isPaused) {
      cleanup();
      state.remaining = Math.max(
        0,
        state.remaining - (Date.now() - state.startTime)
      );
      state.isPaused = true;
    }
  }, [cleanup]);

  const resume = useCallback(() => {
    const state = timerState.current;
    if (state.isPaused && state.remaining > 0) {
      start();
    }
  }, [start]);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return { progress, start, pause, resume, reset };
}


// --- Main Toast Component ---
export const Toast = ({ message, onDone }) => {
  const [open, setOpen] = useState(false);
  const toastDuration = 5000;
  
  const { progress, start, pause, resume, reset } = useProgressTimer({
    duration: toastDuration,
    onComplete: () => {
        setOpen(false);
        // Wait for fade-out animation before clearing the message in the parent
        setTimeout(() => onDone(), 300);
    },
  });

  // Effect to show the toast when a new message arrives from the parent
  useEffect(() => {
    if (message) {
      setOpen(true);
      reset();
      start();
    } else {
      setOpen(false);
    }
  }, [message, reset, start]);

  const handleClose = () => {
    setOpen(false);
    setTimeout(() => onDone(), 300);
  }

  return (
    <div className="toast-viewport">
        <div 
            className={`toast ${open ? 'visible' : ''}`}
            onMouseEnter={pause}
            onMouseLeave={resume}
        >
            <div className="toast-content">
                <CircleCheckIcon className="toast-icon" />
                <div className="toast-text-wrapper">
                    <h3 className="toast-title">Notification</h3>
                    <p className="toast-description">{message}</p>
                </div>
                <button
                    className="toast-close-button"
                    aria-label="Close notification"
                    onClick={handleClose}
                >
                    <XIcon />
                </button>
            </div>
            <div className="toast-progress-bar-container" aria-hidden="true">
                <div
                    className="toast-progress-bar"
                    style={{
                        width: `${(progress / toastDuration) * 100}%`,
                    }}
                />
            </div>
        </div>
    </div>
  );
};
