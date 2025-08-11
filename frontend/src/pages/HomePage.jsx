// src/pages/HomePage.jsx
import React, { useEffect, useRef, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { DashboardCard } from '../components/DashboardCard';

const SyslogIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 6h16M4 12h16M4 18h12"/>
  </svg>
);
const NetflowIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12h20M12 2v20"/>
  </svg>
);
const NetconsoleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 16h4"/>
  </svg>
);
const SnmpIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 16V8a2 2 0 0 0-1-1.73L13 2.27a2 2 0 0 0-2 0L4 6.27A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
  </svg>
);
const StatusIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>
  </svg>
);

const HistoricalVolumeChart = ({ data }) => (
  <div className="dashboard-chart-card">
    <div className="chart-header">
      <div className="chart-title-group">
        <h3 className="chart-title">24-Hour Packet Volume</h3>
        <p className="chart-description">Total packets aggregated per minute</p>
      </div>
    </div>
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
          <defs>
            <linearGradient id="colorSyslog" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity="0.8" />
              <stop offset="95%" stopColor="#8884d8" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="colorNetflow" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#82ca9d" stopOpacity="0.8" />
              <stop offset="95%" stopColor="#82ca9d" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="colorNetconsole" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity="0.8" />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="colorSnmp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34d399" stopOpacity="0.8" />
              <stop offset="95%" stopColor="#34d399" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-dark)" />
          <XAxis dataKey="time" tick={{ fill: 'var(--color-text-secondary-dark)', fontSize: 12 }} interval="preserveStartEnd" />
          <YAxis tick={{ fill: 'var(--color-text-secondary-dark)', fontSize: 12 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ backgroundColor: 'var(--color-surface-dark)', borderColor: 'var(--color-border-dark)', borderRadius: 8 }}
            labelStyle={{ fontWeight: 'bold' }}
          />
          <Legend />
          <Area type="monotone" dataKey="syslog" stroke="#8884d8" fillOpacity={1} fill="url(#colorSyslog)" />
          <Area type="monotone" dataKey="netflow" stroke="#82ca9d" fillOpacity={1} fill="url(#colorNetflow)" />
          <Area type="monotone" dataKey="netconsole" stroke="#f59e0b" fillOpacity={1} fill="url(#colorNetconsole)" />
          <Area type="monotone" dataKey="snmp" stroke="#34d399" fillOpacity={1} fill="url(#colorSnmp)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </div>
);

export const HomePage = ({ serviceStatus, onNavigate }) => {
  const [chartData, setChartData] = useState([]);
  const liveCounts = useRef({ syslog: 0, netflow: 0, netconsole: 0, snmp: 0 });

  // historical
  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        const r = await fetch('/api/graph/volume/');
        if (!r.ok) return;
        const j = await r.json();
        setChartData(j);
      } catch {}
    };
    fetchHistoricalData();
  }, []);

  // live increments (no re-render on each message)
  useEffect(() => {
    const url = import.meta.env.VITE_SYSLOG_WEBSOCKET_URL;
    if (!url) return;
    const ws = new WebSocket(url);
    ws.onmessage = () => { liveCounts.current.syslog += 1; };
    return () => ws.close();
  }, []);
  useEffect(() => {
    const url = import.meta.env.VITE_NETFLOW_WEBSOCKET_URL;
    if (!url) return;
    const ws = new WebSocket(url);
    ws.onmessage = () => { liveCounts.current.netflow += 1; };
    return () => ws.close();
  }, []);
  useEffect(() => {
    const url = import.meta.env.VITE_NETCONSOLE_WEBSOCKET_URL || 'ws://127.0.0.1:8000/ws/netconsole/';
    const ws = new WebSocket(url);
    ws.onmessage = () => { liveCounts.current.netconsole += 1; };
    return () => ws.close();
  }, []);
  useEffect(() => {
    const url = import.meta.env.VITE_SNMP_WEBSOCKET_URL || 'ws://127.0.0.1:8000/ws/snmp/';
    const ws = new WebSocket(url);
    ws.onmessage = () => { liveCounts.current.snmp += 1; };
    return () => ws.close();
  }, []);

  // rollup to chart every 5s
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const label = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
      const inc = liveCounts.current;
      if (inc.syslog || inc.netflow || inc.netconsole || inc.snmp) {
        setChartData((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.time === label) {
            next[next.length - 1] = {
              ...last,
              syslog: (last.syslog || 0) + inc.syslog,
              netflow: (last.netflow || 0) + inc.netflow,
              netconsole: (last.netconsole || 0) + inc.netconsole,
              snmp: (last.snmp || 0) + inc.snmp,
            };
          } else {
            next.push({ time: label, syslog: inc.syslog, netflow: inc.netflow, netconsole: inc.netconsole, snmp: inc.snmp });
          }
          liveCounts.current = { syslog: 0, netflow: 0, netconsole: 0, snmp: 0 };
          return next.slice(-1440);
        });
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      {/* Primary card */}
      <div className="dashboard-grid">
        <DashboardCard
          icon={<StatusIcon />}
          title="System Status"
          description="Live status of all collector services."
          statusText={
            <div className="status-grid">
              <span>Syslog:</span> <strong className={`status-text-${serviceStatus.syslog}`}>{serviceStatus.syslog}</strong>
              <span>Netflow:</span> <strong className={`status-text-${serviceStatus.netflow}`}>{serviceStatus.netflow}</strong>
              <span>Netconsole:</span> <strong className={`status-text-${serviceStatus.netconsole}`}>{serviceStatus.netconsole}</strong>
              <span>SNMP:</span> <strong className={`status-text-${serviceStatus.snmp}`}>{serviceStatus.snmp}</strong>
            </div>
          }
        />
      </div>

      {/* Graph */}
      <HistoricalVolumeChart data={chartData} />

      {/* Collectors grid */}
      <div className="dashboard-grid">
        <DashboardCard
          icon={<SyslogIcon />}
          title="Syslog Viewer"
          description="View and analyze live Syslog data."
          status={serviceStatus.syslog}
          onClick={() => onNavigate('syslog')}
        />
        <DashboardCard
          icon={<NetflowIcon />}
          title="Netflow Analyzer"
          description="View and analyze live Netflow data."
          status={serviceStatus.netflow}
          onClick={() => onNavigate('netflow')}
        />
        <DashboardCard
          icon={<NetconsoleIcon />}
          title="Netconsole Viewer"
          description="View and analyze live Netconsole data."
          status={serviceStatus.netconsole}
          onClick={() => onNavigate('netconsole')}
        />
        <DashboardCard
          icon={<SnmpIcon />}
          title="SNMP Trap Monitor"
          description="View and analyze live SNMP traps."
          status={serviceStatus.snmp}
          onClick={() => onNavigate('snmp')}
        />
      </div>
    </div>
  );
};
