import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { DashboardCard } from '../components/DashboardCard';
import { getCookie, setCookie } from '../utils/cookies';

// --- SVG Icons (No Change) ---
const SyslogIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 6h16M4 12h16M4 18h12"/></svg>;
const NetflowIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12h20M12 2v20"/></svg>;
const StatusIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>;
const SettingsIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 0 2l-.15.08a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l-.22-.38a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1 0-2l-.15-.08a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>;


// --- New, Professional Chart Component ---
const HistoricalVolumeChart = ({ data }) => {
  return (
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
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1}/>
              </linearGradient>
              <linearGradient id="colorNetflow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#82ca9d" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-dark)" />
            <XAxis dataKey="time" tick={{ fill: 'var(--color-text-secondary-dark)', fontSize: 12 }} interval="preserveStartEnd" />
            <YAxis tick={{ fill: 'var(--color-text-secondary-dark)', fontSize: 12 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface-dark)',
                borderColor: 'var(--color-border-dark)',
                borderRadius: '8px'
              }}
              labelStyle={{ fontWeight: 'bold' }}
            />
            <Legend />
            <Area type="monotone" dataKey="syslog" stroke="#8884d8" fillOpacity={1} fill="url(#colorSyslog)" />
            <Area type="monotone" dataKey="netflow" stroke="#82ca9d" fillOpacity={1} fill="url(#colorNetflow)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};


export const HomePage = ({ serviceStatus, onNavigate }) => {
  const [chartData, setChartData] = useState([]);
  // Use a ref to accumulate live counts without causing re-renders
  const liveCounts = useRef({ syslog: 0, netflow: 0 });

  // Fetch historical data only once when the component first loads
  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        const response = await fetch('/api/graph/volume/');
        const data = await response.json();
        setChartData(data);
      } catch (error) {
        console.error("Failed to fetch historical chart data:", error);
      }
    };
    fetchHistoricalData();
  }, []);

  // WebSocket listener for Syslog - just increments a counter
  useEffect(() => {
    const socket = new WebSocket(import.meta.env.VITE_SYSLOG_WEBSOCKET_URL);
    socket.onmessage = () => { liveCounts.current.syslog += 1; };
    return () => socket.close();
  }, []);

  // WebSocket listener for Netflow - just increments a counter
  useEffect(() => {
    const socket = new WebSocket(import.meta.env.VITE_NETFLOW_WEBSOCKET_URL);
    socket.onmessage = () => { liveCounts.current.netflow += 1; };
    return () => socket.close();
  }, []);

  // A separate timer updates the chart state periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const currentTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
      
      // Only update if there's new data to add
      if (liveCounts.current.syslog > 0 || liveCounts.current.netflow > 0) {
        setChartData(prevData => {
          const newData = [...prevData];
          const lastPoint = newData[newData.length - 1];

          if (lastPoint && lastPoint.time === currentTime) {
            // If the last data point is for the current minute, update it
            const updatedPoint = {
              ...lastPoint,
              syslog: lastPoint.syslog + liveCounts.current.syslog,
              netflow: lastPoint.netflow + liveCounts.current.netflow,
            };
            newData[newData.length - 1] = updatedPoint;
          } else {
            // Otherwise, add a new data point for the new minute
            newData.push({
              time: currentTime,
              syslog: liveCounts.current.syslog,
              netflow: liveCounts.current.netflow,
            });
          }
          
          // Reset the live counters
          liveCounts.current = { syslog: 0, netflow: 0 };
          
          // Return the updated array, keeping the last 24 hours of data
          return newData.slice(-1440);
        });
      }
    }, 5000); // Update the chart every 5 seconds with accumulated data

    return () => clearInterval(interval);
  }, []); // This effect runs only once

  return (
    <div className="dashboard-container">
      <div className="dashboard-grid">
        <DashboardCard
          icon={<StatusIcon />}
          title="System Status"
          description="Live status of all collector services."
          statusText={
            <div className="status-grid">
              <span>Syslog:</span> <strong className={`status-text-${serviceStatus.syslog}`}>{serviceStatus.syslog}</strong>
              <span>Netflow:</span> <strong className={`status-text-${serviceStatus.netflow}`}>{serviceStatus.netflow}</strong>
            </div>
          }
        />
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
          icon={<SettingsIcon />}
          title="Settings"
          description="Configure collectors and system settings."
          statusText="Coming Soon"
          onClick={() => {}}
        />
      </div>

      <HistoricalVolumeChart data={chartData} />
    </div>
  );
};
