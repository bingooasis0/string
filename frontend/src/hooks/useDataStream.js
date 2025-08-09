import { useState, useEffect } from 'react';

export const useDataStream = (websocketUrl, onMessage) => {
  const [status, setStatus] = useState('Connecting...');

  useEffect(() => {
    const socket = new WebSocket(websocketUrl);
    socket.onopen = () => setStatus('Connected');
    socket.onclose = () => setStatus('Disconnected');
    socket.onerror = () => setStatus('Error');
    
    socket.onmessage = (event) => {
      const newItem = JSON.parse(event.data);
      if (onMessage) {
        onMessage(newItem);
      }
    };

    return () => socket.close();
  }, [websocketUrl, onMessage]);

  return { status };
};
