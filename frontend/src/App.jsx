import { useEffect, useRef, useState } from 'react';
import './App.css';

import { HomePage } from './pages/HomePage';
import { SyslogPage } from './pages/SyslogPage';
import { NetflowPage } from './pages/NetflowPage';
import NetconsolePage from './pages/NetconsolePage';
import SnmpPage from './pages/SnmpPage';

import { Modal } from './components/Modal';
import { Toast } from './components/Toast';
import { ConfirmationToast } from './components/ConfirmationToast';
import { getCookie, setCookie } from './utils/cookies';

export default function App() {
  // theme
  const [theme, setTheme] = useState(getCookie('theme') || 'dark');

  // nav + status
  const [currentPage, setCurrentPage] = useState('home');
  const [serviceStatus, setServiceStatus] = useState({
    syslog: 'down',
    netflow: 'down',
    netconsole: 'down',
    snmp: 'down',
  });

  // ui state
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  const timersRef = useRef({});
  const showToast = (message) => setToastMessage(message);

  // start/stop for current service
  const handleServicesClick = async () => {
    const serviceToControl = currentPage;
    if (!['syslog', 'netflow', 'netconsole', 'snmp'].includes(serviceToControl)) return;

    const running = serviceStatus[serviceToControl] === 'running';
    const action = running ? 'stop' : 'start';

    try {
      showToast(`Requesting to ${action} ${serviceToControl} service...`);
      const res = await fetch(`/api/service/${action}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ service: serviceToControl }),
      });
      const json = await res.json();
      if (res.ok) {
        showToast(json.message || `${action} sent`);
        if (action === 'stop') {
          setServiceStatus((p) => ({ ...p, [serviceToControl]: 'down' }));
        }
      } else {
        showToast(`Error: ${json.message || res.statusText}`);
      }
    } catch {
      showToast('Network error while controlling service.');
    }
  };

  const handleStopAllServices = async () => {
    try {
      showToast('Requesting to stop all services...');
      const res = await fetch('/api/service/stop_all/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      });
      const json = await res.json();
      if (res.ok) {
        showToast(json.message || 'Stopped all services.');
        setServiceStatus({ syslog: 'down', netflow: 'down', netconsole: 'down', snmp: 'down' });
      } else {
        showToast(`Error: ${json.message || res.statusText}`);
      }
    } catch {
      showToast('Network error while stopping services.');
    }
  };

  const handlePurgeData = () => {
    setConfirmAction(() => executePurge);
    setIsConfirmOpen(true);
  };

  const executePurge = async () => {
    try {
      showToast('Purging all data from database...');
      const res = await fetch('/api/service/purge_all/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      });
      const json = await res.json();
      if (res.ok) {
        showToast(json.message || 'Purge complete.');
        setIsDebugModalOpen(false);
      } else {
        showToast(`Error: ${json.message || res.statusText}`);
      }
    } catch {
      showToast('Network error while purging.');
    }
  };

  const handleStartAllServices = async () => {
    try {
      showToast('Requesting to start all services...');
      const services = ['syslog', 'netflow', 'netconsole', 'snmp'];
      const results = await Promise.all(
        services.map((s) =>
          fetch('/api/service/start/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ service: s }),
          })
        )
      );
      const allOk = results.every((r) => r.ok);
      if (allOk) {
        showToast('Started all collectors.');
        setServiceStatus((prev) => ({ ...prev, syslog: 'running', netflow: 'running', netconsole: 'running', snmp: 'running' }));
      } else {
        const msgs = await Promise.all(results.map((r) => r.json().catch(() => ({ message: r.statusText }))));
        showToast(`Some collectors failed: ${msgs.map((m) => m?.message || 'error').join(', ')}`);
      }
    } catch {
      showToast('Network error while starting services.');
    }
  };

  const handleConfirm = () => {
    if (confirmAction) confirmAction();
    setIsConfirmOpen(false);
    setConfirmAction(null);
  };
  const handleCancel = () => {
    setIsConfirmOpen(false);
    setConfirmAction(null);
  };

  // status websocket
  useEffect(() => {
    const url = import.meta.env.VITE_STATUS_WEBSOCKET_URL || 'ws://127.0.0.1:8000/ws/status/';
    const ws = new WebSocket(url);
    ws.onmessage = (evt) => {
      const { service, status } = JSON.parse(evt.data);
      setServiceStatus((p) => ({ ...p, [service]: status }));
      clearTimeout(timersRef.current[service]);
      timersRef.current[service] = setTimeout(() => {
        setServiceStatus((p) => ({ ...p, [service]: 'down' }));
      }, 10000);
    };
    return () => {
      ws.close();
      Object.values(timersRef.current).forEach(clearTimeout);
    };
  }, []);

  // optional poller (if enabled on backend)
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const r = await fetch('/api/service/status/');
        if (r.ok) {
          setServiceStatus(await r.json());
        }
      } catch {}
    }, 4000);
    return () => clearInterval(id);
  }, []);

  // persist theme
  useEffect(() => setCookie('theme', theme, 365), [theme]);
  const toggleTheme = () => setTheme((p) => (p === 'light' ? 'dark' : 'light'));

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage serviceStatus={serviceStatus} onNavigate={setCurrentPage} />;
      case 'syslog':
        return <SyslogPage collectorStatus={serviceStatus.syslog} />;
      case 'netflow':
        return <NetflowPage collectorStatus={serviceStatus.netflow} />;
      case 'netconsole':
        return <NetconsolePage collectorStatus={serviceStatus.netconsole} />;
      case 'snmp':
        return <SnmpPage collectorStatus={serviceStatus.snmp} />;
      default:
        return <HomePage serviceStatus={serviceStatus} onNavigate={setCurrentPage} />;
    }
  };

  const hasControllableService = ['syslog', 'netflow', 'netconsole', 'snmp'].includes(currentPage);
  const isCurrentServiceRunning = hasControllableService && serviceStatus[currentPage] === 'running';

  return (
    <div className={`App ${theme}`}>
      <header className="header">
        <div className="header-title">
          string
          <img src="/string.png" alt="String Project Logo" className="header-logo" />
        </div>

        <nav className="nav">
          <button onClick={() => setCurrentPage('home')} className={`nav-button ${currentPage === 'home' ? 'active' : ''}`}>Home</button>
          <button onClick={() => setCurrentPage('syslog')} className={`nav-button ${currentPage === 'syslog' ? 'active' : ''}`}>Syslog</button>
          <button onClick={() => setCurrentPage('netflow')} className={`nav-button ${currentPage === 'netflow' ? 'active' : ''}`}>Netflow</button>
          <button onClick={() => setCurrentPage('netconsole')} className={`nav-button ${currentPage === 'netconsole' ? 'active' : ''}`}>Netconsole</button>
          <button onClick={() => setCurrentPage('snmp')} className={`nav-button ${currentPage === 'snmp' ? 'active' : ''}`}>SNMP</button>
        </nav>

        <div className="header-controls">
          {hasControllableService && (
            <button onClick={handleServicesClick} className="theme-toggle-button">
              {isCurrentServiceRunning ? 'Kill Service' : 'Start Service'}
            </button>
          )}
          <button onClick={() => setIsDebugModalOpen(true)} className="theme-toggle-button">Debug</button>
          <button onClick={toggleTheme} className="theme-toggle-button">
            Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
          </button>
        </div>
      </header>

      <main className="main-content">{renderPage()}</main>

      <Modal isOpen={isDebugModalOpen} onClose={() => setIsDebugModalOpen(false)} title="Debug Information">
        <p>Current application state:</p>
        <pre><code>{JSON.stringify({ currentPage, theme, serviceStatus }, null, 2)}</code></pre>

        {/* Start all (green) */}
        <div className="modal-actions" style={{ marginBottom: 12 }}>
          <button
            onClick={handleStartAllServices}
            className="debug-button success"
            style={{ backgroundColor: 'var(--color-success, #0F4D0F)', color: 'white' }}
          >
            Start All Collector Services
          </button>
        </div>

        {/* Stop + Purge (red) */}
        <div className="modal-actions">
          <button onClick={handleStopAllServices} className="debug-button danger">Stop All Collector Services</button>
          <button onClick={handlePurgeData} className="debug-button danger">Purge All Database Records</button>
        </div>
      </Modal>

      <Toast message={toastMessage} onDone={() => setToastMessage('')} />
      <ConfirmationToast
        isOpen={isConfirmOpen}
        message="Are you sure you want to permanently delete all records? This cannot be undone."
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </div>
  );
}
