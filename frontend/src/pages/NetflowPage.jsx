import React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useDataStream } from '../hooks/useDataStream';
import { DataTable } from '../components/DataTable';

export const NetflowPage = () => {
  const [packets, setPackets] = useState([]);
  
  const onMessage = useCallback((newPacket) => {
    setPackets(prevPackets => [newPacket, ...prevPackets].slice(0, 200));
  }, []);

  const { status: streamStatus } = useDataStream(import.meta.env.VITE_NETFLOW_WEBSOCKET_URL, onMessage);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const response = await fetch('/api/netflow/recent/');
        const initialData = await response.json();
        setPackets(initialData);
      } catch (error) {
        console.error("Failed to fetch initial netflow data:", error);
      }
    };
    fetchInitialData();
  }, []);

  return <DataTable packets={packets} />;
};
