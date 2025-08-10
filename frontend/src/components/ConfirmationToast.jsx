import React from 'react';

export const ConfirmationToast = ({ message, onConfirm, onCancel, isOpen }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="confirmation-toast-backdrop">
      <div className="confirmation-toast">
        <p className="confirmation-message">{message}</p>
        <div className="confirmation-buttons">
          <button onClick={onCancel} className="confirm-button cancel">
            Cancel
          </button>
          <button onClick={onConfirm} className="confirm-button confirm">
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
};
