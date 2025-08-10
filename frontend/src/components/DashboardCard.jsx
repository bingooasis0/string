import React from 'react';

export const DashboardCard = ({ icon, title, description, status, onClick, statusText }) => {
  const getStatusClass = (s) => (s === 'running' ? 'running' : 'down');

  // Add a class to make non-clickable cards appear disabled
  const cardClasses = `dashboard-card ${!onClick ? 'disabled' : ''}`;

  return (
    <div onClick={onClick} className={cardClasses}>
      <div className="card-header">
        <div className="card-icon">{icon}</div>
        <h3 className="card-title">{title}</h3>
      </div>
      <p className="card-description">{description}</p>
      <div className="card-footer">
        {status && (
          <div className="card-status">
            <span className={`service-indicator ${getStatusClass(status)}`}></span>
            Status: <strong>{status}</strong>
          </div>
        )}
        {statusText && (
          <div className="card-status-text">
            {statusText}
          </div>
        )}
      </div>
    </div>
  );
};
