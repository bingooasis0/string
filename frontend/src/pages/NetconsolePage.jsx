import React from 'react'
import { useState, useEffect, useCallback } from 'react'
import { useDataStream } from '../hooks/useDataStream'
import { DataTable } from '../components/DataTable'

export default function NetconsolePage() {
  const [packets, setPackets] = useState([])

  const onMessage = useCallback((pkt) => {
    setPackets((prev) => [pkt, ...prev].slice(0, 200))
  }, [])

  const { status: streamStatus } = useDataStream(
    import.meta.env.VITE_NETCONSOLE_WEBSOCKET_URL,
    onMessage
  )

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/api/netconsole/recent/')
        if (!r.ok) return
        const j = await r.json()
        setPackets(j)
      } catch {}
    }
    load()
  }, [])

  return (
    <DataTable
      title="Netconsole"
      packets={packets}
      streamStatus={streamStatus}
      collectorStatus={'running'}
    />
  )
}
