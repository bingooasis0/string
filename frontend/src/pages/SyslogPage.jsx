import React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useDataStream } from '../hooks/useDataStream';
import { DataTable } from '../components/DataTable';

export const SyslogPage = ({ collectorStatus }) => {
  const [packets, setPackets] = useState([]);
  
  const onMessage = useCallback((newPacket) => {
    setPackets(prevPackets => [newPacket, ...prevPackets].slice(0, 200));
  }, []);

  const { status: streamStatus } = useDataStream(import.meta.env.VITE_SYSLOG_WEBSOCKET_URL, onMessage);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const response = await fetch('/api/syslog/recent/');
        const initialData = await response.json();
        setPackets(initialData);
      } catch (error) {
        console.error("Failed to fetch initial syslog data:", error);
      }
    };
    fetchInitialData();
  }, []);

  return <DataTable title="Syslog" packets={packets} streamStatus={streamStatus} collectorStatus={collectorStatus} />;
};
