import { useState, useEffect } from 'react';
import './App.css';
import { HomePage } from './pages/HomePage';
import { SyslogPage } from './pages/SyslogPage';
import { NetflowPage } from './pages/NetflowPage';
import { Modal } from './components/Modal';
import { Toast } from './components/Toast';
import { ConfirmationToast } from './components/ConfirmationToast';
import { getCookie, setCookie } from './utils/cookies'; // Import cookie helpers

function App() {
  // THIS IS THE FIX:
  // Read the theme from a cookie. If it doesn't exist, default to 'dark'.
  const [theme, setTheme] = useState(getCookie('theme') || 'dark');
  
  const [currentPage, setCurrentPage] = useState('home');
  const [serviceStatus, setServiceStatus] = useState({ syslog: 'down', netflow: 'down' });
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  const showToast = (message) => {
    setToastMessage(message);
  };

  const handleServicesClick = async () => {
    const serviceToControl = currentPage;
    if (serviceToControl === 'home') return;
    
    const isServiceRunning = serviceStatus[serviceToControl] === 'running';
    const action = isServiceRunning ? 'stop' : 'start';
    
    try {
      showToast(`Requesting to ${action} ${serviceToControl} service...`);
      const response = await fetch(`/api/service/${action}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ service: serviceToControl }),
      });

      const result = await response.json();
      
      if (response.ok) {
        showToast(result.message);
        if (action === 'stop') {
            setServiceStatus(prev => ({ ...prev, [serviceToControl]: 'down' }));
        }
      } else {
        showToast(`Error: ${result.message}`);
      }
    } catch (error) {
      showToast('A network error occurred while controlling the service.');
      console.error("Service control error:", error);
    }
  };

  const handleStopAllServices = async () => {
    try {
      showToast("Requesting to stop all services...");
      const response = await fetch('/api/service/stop_all/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
      });
      const result = await response.json();
      if (response.ok) {
        showToast(result.message);
        setServiceStatus({ syslog: 'down', netflow: 'down' });
      } else {
        showToast(`Error: ${result.message}`);
      }
    } catch (error) {
        showToast('A network error occurred while stopping services.');
        console.error("Stop all services error:", error);
    }
  };

  const handlePurgeData = () => {
    setConfirmAction(() => () => executePurge());
    setIsConfirmOpen(true);
  };

  const executePurge = async () => {
    try {
        showToast("Purging all data from database...");
        const response = await fetch('/api/service/purge_all/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message);
            setIsDebugModalOpen(false);
        } else {
            showToast(`Error: ${result.message}`);
        }
    } catch (error) {
        showToast('A network error occurred while purging data.');
        console.error("Purge data error:", error);
    }
  };

  const handleConfirm = () => {
    if (confirmAction) {
        confirmAction();
    }
    setIsConfirmOpen(false);
    setConfirmAction(null);
  };

  const handleCancel = () => {
    setIsConfirmOpen(false);
    setConfirmAction(null);
  };

  useEffect(() => {
    const socket = new WebSocket(import.meta.env.VITE_STATUS_WEBSOCKET_URL);
    const timers = {};
    socket.onmessage = (event) => {
      const { service, status } = JSON.parse(event.data);
      setServiceStatus(prev => ({ ...prev, [service]: status }));
      clearTimeout(timers[service]);
      
      if (status === 'running') {
        timers[service] = setTimeout(() => {
          setServiceStatus(prev => ({ ...prev, [service]: 'down' }));
        }, 5000);
      }
    };
    return () => {
      socket.close();
      Object.values(timers).forEach(clearTimeout);
    };
  }, []);

  // THIS IS THE FIX:
  // When the theme changes, we save the new value in a cookie.
  useEffect(() => {
    setCookie('theme', theme, 365);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => (prev === 'light' ? 'dark' : 'light'));

  const renderPage = () => {
    switch (currentPage) {
      case 'home': return <HomePage serviceStatus={serviceStatus} onNavigate={setCurrentPage} />;
      case 'syslog': return <SyslogPage collectorStatus={serviceStatus.syslog} />;
      case 'netflow': return <NetflowPage collectorStatus={serviceStatus.netflow} />;
      default: return <HomePage serviceStatus={serviceStatus} onNavigate={setCurrentPage} />;
    }
  };

  const hasControllableService = currentPage === 'syslog' || currentPage === 'netflow';
  const isCurrentServiceRunning = hasControllableService && serviceStatus[currentPage] === 'running';

  return (
    <div className={`App ${theme}`}>
      <header className="header">
        <div className="header-title">
          string
          <img src="/string.png" alt="String Project Logo" className="header-logo" />
        </div>
        <nav className="nav">
          <button onClick={() => setCurrentPage('home')} className={`nav-button ${currentPage === 'home' && 'active'}`}>Home</button>
          <button onClick={() => setCurrentPage('syslog')} className={`nav-button ${currentPage === 'syslog' && 'active'}`}>Syslog</button>
          <button onClick={() => setCurrentPage('netflow')} className={`nav-button ${currentPage === 'netflow' && 'active'}`}>Netflow</button>
        </nav>
        <div className="header-controls">
          {hasControllableService && (
            <button onClick={handleServicesClick} className="theme-toggle-button">
              {isCurrentServiceRunning ? 'Kill Service' : 'Start Service'}
            </button>
          )}
          <button onClick={() => setIsDebugModalOpen(true)} className="theme-toggle-button">
            Debug
          </button>
          <button onClick={toggleTheme} className="theme-toggle-button">
            Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
          </button>
        </div>
      </header>
      <main className="main-content">
        {renderPage()}
      </main>
      
      <Modal 
        isOpen={isDebugModalOpen} 
        onClose={() => setIsDebugModalOpen(false)}
        title="Debug Information"
      >
        <p>Current application state:</p>
        <pre>
          <code>
            {JSON.stringify({
              currentPage,
              theme,
              serviceStatus
            }, null, 2)}
          </code>
        </pre>
        <div className="modal-actions">
            <button onClick={handleStopAllServices} className="debug-button danger">
                Stop All Collector Services
            </button>
            <button onClick={handlePurgeData} className="debug-button danger">
                Purge All Database Records
            </button>
        </div>
      </Modal>

      <Toast 
        message={toastMessage} 
        onDone={() => setToastMessage('')}
      />

      <ConfirmationToast
        isOpen={isConfirmOpen}
        message="Are you sure you want to permanently delete all records? This cannot be undone."
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </div>
  );
}

export default App;
