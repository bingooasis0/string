import React from 'react'

export const DataTable = ({ title, packets = [], streamStatus, collectorStatus, columns }) => {
  const getStatusClass = (s) => {
    if (s === 'Connected' || s === 'running') return 'connected'
    if (s === 'Disconnected' || s === 'Error' || s === 'down') return 'disconnected'
    return 'connecting'
  }

  const defaultCols = [
    { key: 'id', label: 'ID' },
    { key: 'timestamp', label: 'Timestamp' },
    { key: 'source', label: 'Source' },
    { key: 'protocol', label: 'Protocol' },
    { key: 'info', label: 'Info' }
  ]
  const cols = columns && columns.length ? columns : defaultCols

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
              {cols.map((c) => (
                <th key={c.key}>{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {packets.map((row) => (
              <tr key={row.id}>
                {cols.map((c) => (
                  <td key={c.key}>
                    {c.key === 'timestamp' && !columns
                      ? new Date(row[c.key]).toLocaleTimeString()
                      : row[c.key] ?? ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

export default DataTable
