import struct
import ipaddress
from datetime import datetime, timezone, timedelta

V9 = 9
IPFIX = 10

V9_FIELDS = {
    1:"bytes",2:"packets",4:"protocol",5:"tos",6:"tcp_flags",7:"src_port",8:"src_ip",
    9:"next_hop",10:"input_if",11:"dst_port",12:"dst_ip",14:"output_if",
    15:"src_as",16:"dst_as",21:"last_switched",22:"first_switched",55:"vlan_id_in",56:"vlan_id_out"
}

IPFIX_FIELDS = {
    1:"bytes",2:"packets",4:"protocol",5:"tos",6:"tcp_flags",7:"src_port",8:"src_ip",
    10:"input_if",11:"dst_port",12:"dst_ip",14:"output_if",15:"src_as",16:"dst_as",
    27:"next_hop",148:"flow_start",149:"flow_end",152:"flow_start_ms",153:"flow_end_ms"
}

class TemplateCache:
    def __init__(self):
        self.v9 = {}
        self.ipfix = {}
    def put_v9(self, exporter, source_id, template_id, fields):
        self.v9[(exporter,source_id,template_id)] = fields
    def get_v9(self, exporter, source_id, template_id):
        return self.v9.get((exporter,source_id,template_id))
    def put_ipfix(self, exporter, odid, template_id, fields):
        self.ipfix[(exporter,odid,template_id)] = fields
    def get_ipfix(self, exporter, odid, template_id):
        return self.ipfix.get((exporter,odid,template_id))

def _u16(b,o): return struct.unpack_from("!H", b, o)[0]
def _u32(b,o): return struct.unpack_from("!I", b, o)[0]
def _u64(b,o): return struct.unpack_from("!Q", b, o)[0]

def _ip4(v): return str(ipaddress.ip_address(v))

def parse_packet(data, exporter_ip, cache: TemplateCache):
    if len(data) < 4: return {"version":None,"flows":[],"notes":["short_packet"]}
    ver = _u16(data,0)
    if ver == V9:
        f,notes = _parse_v9(data, exporter_ip, cache)
        return {"version":V9,"flows":f,"notes":notes}
    if ver == IPFIX:
        f,notes = _parse_ipfix(data, exporter_ip, cache)
        return {"version":IPFIX,"flows":f,"notes":notes}
    return {"version":ver,"flows":[],"notes":["unknown_version"]}

def _parse_v9(data, exporter_ip, cache):
    notes = []
    if len(data) < 20: return [],["v9_header_too_short"]
    count = _u16(data,2)
    sys_uptime = _u32(data,4)
    unix_secs = _u32(data,8)
    source_id = _u32(data,16)
    ts_export = datetime.fromtimestamp(unix_secs, tz=timezone.utc)
    o = 20
    flows = []
    while o + 4 <= len(data):
        set_id = _u16(data,o); set_len = _u16(data,o+2); o2 = o+4
        if set_len < 4 or o+set_len > len(data):
            notes.append("v9_bad_set_len")
            break
        if set_id == 0:
            while o2 + 4 <= o+set_len:
                tid = _u16(data,o2); fc = _u16(data,o2+2); o2 += 4
                fields = []
                for _ in range(fc):
                    if o2 + 4 > o+set_len: break
                    ftype = _u16(data,o2); flen = _u16(data,o2+2); o2 += 4
                    fields.append((ftype, flen))
                cache.put_v9(exporter_ip, source_id, tid, fields)
            notes.append("v9_template_seen")
        elif set_id == 1:
            notes.append("v9_options_ignored")
        elif set_id >= 256:
            tpl = cache.get_v9(exporter_ip, source_id, set_id)
            if not tpl:
                notes.append(f"v9_data_without_template_{set_id}")
                o = o+set_len
                continue
            rec_len = sum(f[1] for f in tpl)
            rec_o = o2
            while rec_o + rec_len <= o+set_len:
                fv = {}
                idx = rec_o
                for ftype, flen in tpl:
                    buf = data[idx:idx+flen]
                    idx += flen
                    name = V9_FIELDS.get(ftype)
                    if not name: continue
                    if name in ("src_ip","dst_ip","next_hop"):
                        if flen == 4: fv[name] = _ip4(_u32(buf,0))
                        elif flen == 16: fv[name] = str(ipaddress.IPv6Address(buf))
                    elif name in ("bytes","packets","input_if","output_if","src_port","dst_port","protocol","tos","tcp_flags","src_as","dst_as","vlan_id_in","vlan_id_out","first_switched","last_switched"):
                        if flen == 1: fv[name] = buf[0]
                        elif flen == 2: fv[name] = _u16(buf,0)
                        elif flen == 4: fv[name] = _u32(buf,0)
                        elif flen == 8: fv[name] = _u64(buf,0)
                fs = fv.get("first_switched")
                le = fv.get("last_switched")
                flow_start = None
                flow_end = None
                if fs is not None:
                    delta = (sys_uptime - fs) / 1000.0
                    flow_start = ts_export - timedelta(seconds=delta)
                if le is not None:
                    delta = (sys_uptime - le) / 1000.0
                    flow_end = ts_export - timedelta(seconds=delta)
                flows.append({
                    "exporter_ip": exporter_ip,
                    "observation_domain_id": source_id,
                    "template_id": set_id,
                    "flow_start": flow_start,
                    "flow_end": flow_end,
                    "src_ip": fv.get("src_ip"),
                    "dst_ip": fv.get("dst_ip"),
                    "src_port": fv.get("src_port"),
                    "dst_port": fv.get("dst_port"),
                    "protocol": fv.get("protocol"),
                    "tos": fv.get("tos"),
                    "tcp_flags": fv.get("tcp_flags"),
                    "packets": fv.get("packets"),
                    "bytes": fv.get("bytes"),
                    "input_if": fv.get("input_if"),
                    "output_if": fv.get("output_if"),
                    "vlan_id_in": fv.get("vlan_id_in"),
                    "vlan_id_out": fv.get("vlan_id_out"),
                    "next_hop": fv.get("next_hop"),
                    "src_as": fv.get("src_as"),
                    "dst_as": fv.get("dst_as"),
                })
                rec_o += rec_len
        o = o+set_len
    return flows,notes

def _parse_ipfix(data, exporter_ip, cache):
    notes = []
    if len(data) < 16: return [],["ipfix_header_too_short"]
    length = _u16(data,2)
    export_time = _u32(data,4)
    odid = _u32(data,12)
    ts_export = datetime.fromtimestamp(export_time, tz=timezone.utc)
    o = 16
    flows = []
    while o + 4 <= len(data) and o < length:
        set_id = _u16(data,o); set_len = _u16(data,o+2); o2 = o+4
        if set_len < 4 or o+set_len > len(data):
            notes.append("ipfix_bad_set_len")
            break
        if set_id == 2:
            while o2 + 4 <= o+set_len:
                tid = _u16(data,o2); fc = _u16(data,o2+2); o2 += 4
                fields = []
                for _ in range(fc):
                    if o2 + 4 > o+set_len: break
                    ie = _u16(data,o2); flen = _u16(data,o2+2); o2 += 4
                    if ie & 0x8000:
                        if o2 + 4 > o+set_len: break
                        o2 += 4
                        ie = ie & 0x7FFF
                    fields.append((ie, flen))
                cache.put_ipfix(exporter_ip, odid, tid, fields)
            notes.append("ipfix_template_seen")
        elif set_id == 3:
            notes.append("ipfix_options_ignored")
        elif set_id >= 256:
            tpl = cache.get_ipfix(exporter_ip, odid, set_id)
            if not tpl:
                notes.append(f"ipfix_data_without_template_{set_id}")
                o = o+set_len
                continue
            rec_o = o2
            while rec_o < o+set_len:
                fv = {}
                idx = rec_o
                for ie, flen in tpl:
                    if flen == 65535:
                        l = data[idx]
                        idx += 1
                        if l == 255:
                            l = _u16(data, idx)
                            idx += 2
                        buf = data[idx:idx+l]
                        idx += l
                    else:
                        buf = data[idx:idx+flen]
                        idx += flen
                    name = IPFIX_FIELDS.get(ie)
                    if not name: continue
                    if name in ("src_ip","dst_ip","next_hop"):
                        if len(buf) == 4: fv[name] = _ip4(_u32(buf,0))
                        elif len(buf) == 16: fv[name] = str(ipaddress.IPv6Address(buf))
                    elif name in ("bytes","packets","input_if","output_if","src_port","dst_port","protocol","tos","tcp_flags","src_as","dst_as"):
                        if len(buf) == 1: fv[name] = buf[0]
                        elif len(buf) == 2: fv[name] = _u16(buf,0)
                        elif len(buf) == 4: fv[name] = _u32(buf,0)
                        elif len(buf) == 8: fv[name] = _u64(buf,0)
                    elif name == "flow_start":
                        fv["flow_start"] = datetime.fromtimestamp(_u32(buf,0), tz=timezone.utc)
                    elif name == "flow_end":
                        fv["flow_end"] = datetime.fromtimestamp(_u32(buf,0), tz=timezone.utc)
                    elif name == "flow_start_ms":
                        fv["flow_start"] = datetime.fromtimestamp(_u64(buf,0)/1000.0, tz=timezone.utc)
                    elif name == "flow_end_ms":
                        fv["flow_end"] = datetime.fromtimestamp(_u64(buf,0)/1000.0, tz=timezone.utc)
                flows.append({
                    "exporter_ip": exporter_ip,
                    "observation_domain_id": odid,
                    "template_id": set_id,
                    "flow_start": fv.get("flow_start"),
                    "flow_end": fv.get("flow_end"),
                    "src_ip": fv.get("src_ip"),
                    "dst_ip": fv.get("dst_ip"),
                    "src_port": fv.get("src_port"),
                    "dst_port": fv.get("dst_port"),
                    "protocol": fv.get("protocol"),
                    "tos": fv.get("tos"),
                    "tcp_flags": fv.get("tcp_flags"),
                    "packets": fv.get("packets"),
                    "bytes": fv.get("bytes"),
                    "input_if": fv.get("input_if"),
                    "output_if": fv.get("output_if"),
                    "vlan_id_in": fv.get("vlan_id_in"),
                    "vlan_id_out": fv.get("vlan_id_out"),
                    "next_hop": fv.get("next_hop"),
                    "src_as": fv.get("src_as"),
                    "dst_as": fv.get("dst_as"),
                })
                if idx == rec_o: break
                rec_o = idx
        o = o+set_len
    return flows,notes
