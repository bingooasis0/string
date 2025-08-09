import { useState, useEffect } from 'react';
import './App.css';
import { HomePage } from './pages/HomePage';
import { SyslogPage } from './pages/SyslogPage';
import { NetflowPage } from './pages/NetflowPage';
import { Modal } from './components/Modal';
import { Toast } from './components/Toast';

function App() {
  const [theme, setTheme] = useState('dark');
  const [currentPage, setCurrentPage] = useState('syslog');
  const [serviceStatus, setServiceStatus] = useState({ syslog: 'down', netflow: 'down' });
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (message) => {
    setToastMessage(message);
  };

  // This is the new function that makes real API calls
  const handleServicesClick = async () => {
    const serviceToControl = currentPage;
    // Home page has no service, so do nothing.
    if (serviceToControl === 'home') {
        showToast("No service to control on the Home page.");
        return;
    }
    
    const isServiceRunning = serviceStatus[serviceToControl] === 'running';
    const action = isServiceRunning ? 'stop' : 'start';
    
    try {
      const response = await fetch(`/api/service/${action}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ service: serviceToControl }),
      });

      const result = await response.json();
      
      if (response.ok) {
        showToast(result.message);
        // Manually set status to 'down' on a kill command for faster UI feedback
        if (action === 'stop') {
            setServiceStatus(prev => ({ ...prev, [serviceToControl]: 'down' }));
        }
      } else {
        showToast(`Error: ${result.message}`);
      }
    } catch (error) {
      showToast('A network error occurred.');
      console.error("Service control error:", error);
    }
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

  const toggleTheme = () => setTheme(prev => (prev === 'light' ? 'dark' : 'light'));

  const renderPage = () => {
    switch (currentPage) {
      case 'home': return <HomePage serviceStatus={serviceStatus} />;
      case 'syslog': return <SyslogPage collectorStatus={serviceStatus.syslog} />;
      case 'netflow': return <NetflowPage collectorStatus={serviceStatus.netflow} />;
      default: return <HomePage serviceStatus={serviceStatus} />;
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
        <p>This is where we can add debug options and information later.</p>
        <pre>
          <code>
            {JSON.stringify({
              currentPage,
              theme,
              serviceStatus
            }, null, 2)}
          </code>
        </pre>
      </Modal>

      <Toast 
        message={toastMessage} 
        onDone={() => setToastMessage('')}
      />
    </div>
  );
}

export default App;
