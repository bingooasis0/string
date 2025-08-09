import React, { useState, useEffect } from 'react';

export const Toast = ({ message, duration = 5000, onDone }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (message) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        // Let the parent know we're done so it can clear the message
        if (onDone) {
          onDone();
        }
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [message, duration, onDone]);

  return (
    <div className={`toast-container ${visible ? 'visible' : ''}`}>
      <div className="toast-message">
        {message}
      </div>
    </div>
  );
};
