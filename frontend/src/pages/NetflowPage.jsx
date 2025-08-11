import React from 'react'
import { useState, useEffect, useCallback, useMemo } from 'react'
import { useDataStream } from '../hooks/useDataStream'
import { DataTable } from '../components/DataTable'

export const NetflowPage = ({ collectorStatus }) => {
  const [packets, setPackets] = useState([])

  const columns = useMemo(
    () => [
      { key: 'id', label: 'ID' },
      { key: 'timestamp', label: 'Timestamp' },
      { key: 'src', label: 'Src' },
      { key: 'dst', label: 'Dst' },
      { key: 'protocol', label: 'Proto' },
      { key: 'packets', label: 'Pkts' },
      { key: 'bytes', label: 'Bytes' },
      { key: 'flow_start', label: 'First Seen' },
      { key: 'duration', label: 'Duration(s)' },
      { key: 'input_if', label: 'InIf' },
      { key: 'output_if', label: 'OutIf' },
      { key: 'vlan_id_in', label: 'VLAN In' },
      { key: 'vlan_id_out', label: 'VLAN Out' },
      { key: 'tos', label: 'TOS' },
      { key: 'tcp_flags', label: 'TCP' },
      { key: 'src_as', label: 'SrcAS' },
      { key: 'dst_as', label: 'DstAS' },
      { key: 'exporter_ip', label: 'Exporter' },
      { key: 'odid', label: 'ODID' }
    ],
    []
  )

  const shape = useCallback((e) => {
    const ts = e.timestamp || e.received_at
    const first = e.flow_start
    const dur =
      e.duration != null
        ? e.duration
        : e.flow_start && e.flow_end
        ? (new Date(e.flow_end) - new Date(e.flow_start)) / 1000
        : ''
    return {
      id: e.id,
      timestamp: ts,
      src: [e.src_ip, e.src_port].filter(Boolean).join(':'),
      dst: [e.dst_ip, e.dst_port].filter(Boolean).join(':'),
      protocol: e.protocol ?? '',
      packets: e.packets ?? 0,
      bytes: e.bytes ?? 0,
      flow_start: first ? first.replace('T', ' ').slice(0, 19) : '',
      duration: dur,
      input_if: e.input_if ?? '',
      output_if: e.output_if ?? '',
      vlan_id_in: e.vlan_id_in ?? '',
      vlan_id_out: e.vlan_id_out ?? '',
      tos: e.tos ?? '',
      tcp_flags: e.tcp_flags ?? '',
      src_as: e.src_as ?? '',
      dst_as: e.dst_as ?? '',
      exporter_ip: e.exporter_ip ?? '',
      odid: e.odid ?? e.observation_domain_id ?? ''
    }
  }, [])

  const onMessage = useCallback(
    (m) => {
      setPackets((prev) => [shape(m), ...prev].slice(0, 200))
    },
    [shape]
  )

  const { status: streamStatus } = useDataStream(
    import.meta.env.VITE_NETFLOW_WEBSOCKET_URL,
    onMessage
  )

  useEffect(() => {
    const load = async () => {
      const r = await fetch('/api/netflow/recent/')
      if (!r.ok) return
      const j = await r.json()
      setPackets(j.map(shape))
    }
    load()
  }, [shape])

  return (
    <DataTable
      title="Netflow"
      packets={packets}
      streamStatus={streamStatus}
      collectorStatus={collectorStatus}
      columns={columns}
    />
  )
}
