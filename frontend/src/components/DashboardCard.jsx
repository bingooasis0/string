import React from 'react'

export function DashboardCard({ icon, title, description, status, statusText, onClick }) {
  const cardClass = `dashboard-card${onClick ? ' clickable' : ''}`
  const dot =
    status === 'running' ? 'dot dot-ok' :
    status === 'down' ? 'dot dot-bad' : 'dot dot-warn'

  return (
    <div className={cardClass} onClick={onClick}>
      <div className="card-head">
        <div className="icon">{icon}</div>
        <div className="title">{title}</div>
      </div>
      <div className="card-body">
        <p className="desc">{description}</p>
        {status !== undefined ? (
          <div className="inline">
            <span className={dot} />
            <span>Status - </span>
            <b>{status}</b>
          </div>
        ) : (
          statusText || null
        )}
      </div>
    </div>
  )
}

export default DashboardCard
