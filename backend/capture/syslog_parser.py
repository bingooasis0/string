# C:\Users\colby\Desktop\String\backend\capture\syslog_parser.py

import re
from datetime import datetime

# --- Individual Parsers ---

def parse_standard_firewall_format(message):
    """
    Parses standard syslog formats that begin with a priority, like firewall logs.
    Example: <13>Aug  7 18:26:11 DreamWest [PREROUTING-DNAT-4]...
    """
    # This regex is more robust and handles the <priority> at the start.
    SYSLOG_REGEX = re.compile(
        r'^\<(\d+)\>' # Group 1: Priority
        r'([a-zA-Z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+' # Group 2: Timestamp
        r'([\w\.-]+)\s+' # Group 3: Hostname
        r'(.*)$' # Group 4: The rest of the message
    )
    match = SYSLOG_REGEX.match(message)
    if not match:
        return None

    groups = match.groups()
    return {
        'priority': int(groups[0]),
        'timestamp': datetime.now().isoformat(),
        'hostname': groups[2].strip(),
        'app_name': 'Firewall', # A sensible default for this format
        'pid': None,
        'message': groups[3].strip()
    }

def parse_ubiquiti_format(message):
    """Parses the specific syslog format from Ubiquiti UniFi devices without a priority tag."""
    UBIQUITI_SYSLOG_REGEX = re.compile(
        r'^([a-zA-Z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'([\w\s\.-]+?)\s+'
        r'(.*)$'
    )
    match = UBIQUITI_SYSLOG_REGEX.match(message)
    if not match:
        return None

    groups = match.groups()
    return {
        'priority': 0,
        'timestamp': datetime.now().isoformat(),
        'hostname': groups[1].strip(),
        'app_name': 'UniFi OS',
        'pid': None,
        'message': groups[2].strip()
    }

# --- Parser Registry ---
PARSER_CHAIN = [
    parse_standard_firewall_format, # Try the firewall format first
    parse_ubiquiti_format,
]

# --- Main Parsing Function ---
def parse_message(message_str):
    for parser_func in PARSER_CHAIN:
        result = parser_func(message_str)
        if result is not None:
            return result
    return None