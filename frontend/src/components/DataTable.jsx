import React from 'react';

export const DataTable = ({ title, packets, streamStatus, collectorStatus }) => {
  const getStatusClass = (s) => {
    if (s === 'Connected' || s === 'running') return 'connected';
    if (s === 'Disconnected' || s === 'Error' || s === 'down') return 'disconnected';
    return 'connecting';
  };

  return (
    <>
      <div className="status-bar">
        <span className="status-item">
          <span className={`status-indicator ${getStatusClass(streamStatus)}`}></span>
          UI Stream: <strong>{streamStatus}</strong>
        </span>
        <span className="status-item">
          <span className={`status-indicator ${getStatusClass(collectorStatus)}`}></span>
          Collector: <strong>{collectorStatus}</strong>
        </span>
      </div>
      <div className="output-box">
        <table className="packet-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Source</th>
              <th>Protocol</th>
              <th>Info</th>
            </tr>
          </thead>
          <tbody>
            {packets.map(p => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{new Date(p.timestamp).toLocaleTimeString()}</td>
                <td>{p.source}</td>
                <td>{p.protocol}</td>
                <td>{p.info}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};
