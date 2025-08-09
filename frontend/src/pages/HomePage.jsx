// C:\Users\colby\Desktop\String\frontend\src\pages\HomePage.jsx
import React from 'react';

export const HomePage = ({ serviceStatus }) => {
  const getStatusClass = (s) => (s === 'running' ? 'connected' : 'disconnected');

  return (
    <div>
      <h2>Service Status</h2>
      <div className="status-bar">
        <span className="status-item">
          <span className={`status-indicator ${getStatusClass(serviceStatus.syslog)}`}></span>
          Syslog Collector: <strong>{serviceStatus.syslog}</strong>
        </span>
        <span className="status-item">
          <span className={`status-indicator ${getStatusClass(serviceStatus.netflow)}`}></span>
          Netflow Collector: <strong>{serviceStatus.netflow}</strong>
        </span>
      </div>
      <p>Welcome to the String Project Hub. Select a service from the navigation to view live data.</p>
    </div>
  );
};