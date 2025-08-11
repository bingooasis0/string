// src/pages/SnmpPage.jsx
import React, { useEffect, useState } from 'react';

const cls = (s) =>
  s === 'Connected' || s === 'running'
    ? 'connected'
    : s === 'Disconnected' || s === 'down'
    ? 'disconnected'
    : 'connecting';

const fmt = (v) => (v === null || v === undefined ? '' : v);

export default function SnmpPage({ collectorStatus }) {
  const [rows, setRows] = useState([]);
  const [streamStatus, setStreamStatus] = useState('Connecting');

  useEffect(() => {
    const run = async () => {
      try {
        const r = await fetch('/api/snmp/recent/');
        if (!r.ok) return;
        setRows(await r.json());
      } catch (e) {
        console.error('Failed to fetch initial SNMP data:', e);
      }
    };
    run();
  }, []);

  useEffect(() => {
    const url = import.meta.env.VITE_SNMP_WEBSOCKET_URL || 'ws://127.0.0.1:8000/ws/snmp/';
    const ws = new WebSocket(url);
    ws.onopen = () => setStreamStatus('Connected');
    ws.onclose = () => setStreamStatus('Disconnected');
    ws.onerror = () => setStreamStatus('Error');
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      setRows((prev) => [m, ...prev].slice(0, 200));
    };
    return () => ws.close();
  }, []);

  return (
    <>
      <div className="status-bar">
        <span className="status-item">
          <span className={`status-indicator ${cls(streamStatus)}`}></span>
          UI Stream: <strong>{streamStatus}</strong>
        </span>
        <span className="status-item">
          <span className={`status-indicator ${cls(collectorStatus)}`}></span>
          Collector: <strong>{collectorStatus}</strong>
        </span>
      </div>

      <div className="output-box">
        <table className="packet-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Source</th>
              <th>Version</th>
              <th>User/Community</th>
              <th>Trap OID</th>
              <th>Uptime</th>
              <th>Context</th>
              <th>Enterprise</th>
              <th>Gen</th>
              <th>Spec</th>
              <th>Security</th>
              <th>Info</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : ''}</td>
                <td>{fmt(r.source_ip)}</td>
                <td>{fmt(r.version)}</td>
                <td>{r.user || r.community || ''}</td>
                <td>{fmt(r.trap_oid)}</td>
                <td>{fmt(r.uptime)}</td>
                <td>{[fmt(r.context_engine_id), fmt(r.context_name)].filter(Boolean).join('/')}</td>
                <td>{fmt(r.enterprise_oid)}</td>
                <td>{fmt(r.generic_trap)}</td>
                <td>{fmt(r.specific_trap)}</td>
                <td>{[fmt(r.security_level), fmt(r.auth_protocol), fmt(r.priv_protocol)].filter(Boolean).join('/')}</td>
                <td style={{ whiteSpace: 'normal' }}>{fmt(r.info)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
