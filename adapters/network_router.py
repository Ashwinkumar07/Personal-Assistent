"""
Tri-Mode Network Router:
Automatically detects the network state and switches seamlessly between:
1. Mode 1: Direct Local Home Wi-Fi (LAN: 192.168.x.x) - 2-5ms latency
2. Mode 2: Private P2P Encrypted Mesh (Tailscale/WireGuard: 100.x.x.x) - 30-50ms latency
3. Mode 3: Local Offline Standalone Mode - 0ms network latency with offline delta syncing on reconnect
"""

import socket
import time
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.request

from core.logger import logger, log_latency
from memory.manager import MemoryManager

class NetworkMode(str, Enum):
    HOME_LAN = "HOME_LAN"         # Direct local Wi-Fi router
    P2P_MESH = "P2P_MESH"         # Tailscale/WireGuard encrypted P2P tunnel
    OFFLINE_STANDALONE = "OFFLINE_STANDALONE" # Zero connectivity, local operations only

class NetworkRouter:
    def __init__(
        self,
        lan_subnet_prefix: str = "192.168.",
        mesh_subnet_prefix: str = "100.",
        memory_manager: Optional[MemoryManager] = None
    ):
        self.lan_subnet_prefix = lan_subnet_prefix
        self.mesh_subnet_prefix = mesh_subnet_prefix
        self.memory = memory_manager or MemoryManager()
        self.current_mode = NetworkMode.OFFLINE_STANDALONE
        self.offline_queue: List[Dict[str, Any]] = []
        self._last_check_time = 0.0
        self.detect_network_mode()

    def get_local_ip_addresses(self) -> List[str]:
        """Fetch all active local network adapter IPs."""
        ips = []
        try:
            hostname = socket.gethostname()
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip = item[4][0]
                if ":" not in ip and not ip.startswith("127."): # IPv4 non-loopback
                    ips.append(ip)
        except Exception as e:
            logger.debug(f"[NETWORK ROUTER] Error detecting IPs: {e}")
        return ips

    def detect_network_mode(self) -> NetworkMode:
        """
        Dynamically determine the active network mode.
        """
        ips = self.get_local_ip_addresses()
        
        # 1. Check for Tailscale / Mesh VPN adapter (usually 100.x.x.x)
        has_mesh = any(ip.startswith(self.mesh_subnet_prefix) for ip in ips)
        # 2. Check for local Home LAN (192.168.x.x or 10.x.x.x)
        has_lan = any(ip.startswith(self.lan_subnet_prefix) or ip.startswith("10.") for ip in ips)

        previous_mode = self.current_mode

        if has_lan:
            self.current_mode = NetworkMode.HOME_LAN
        elif has_mesh:
            self.current_mode = NetworkMode.P2P_MESH
        else:
            self.current_mode = NetworkMode.OFFLINE_STANDALONE

        # If we just came back online from offline mode, trigger auto-sync
        if previous_mode == NetworkMode.OFFLINE_STANDALONE and self.current_mode != NetworkMode.OFFLINE_STANDALONE:
            logger.info(f"[NETWORK ROUTER] Reconnected ({self.current_mode.value})! Triggering offline delta sync...")
            self.flush_offline_delta_sync()

        return self.current_mode

    def queue_offline_update(self, update_type: str, data: Dict[str, Any]) -> None:
        """Store updates made while offline to merge on reconnect."""
        delta = {
            "type": update_type,
            "data": data,
            "timestamp": time.time()
        }
        self.offline_queue.append(delta)
        logger.info(f"[NETWORK ROUTER] Queued offline update ({update_type}). Total queued: {len(self.offline_queue)}")

    def flush_offline_delta_sync(self) -> int:
        """Sync and merge queued offline memories into main database."""
        if not self.offline_queue:
            return 0

        synced_count = 0
        with log_latency("NetworkRouter.flush_offline_delta_sync", f"{len(self.offline_queue)} items"):
            for delta in self.offline_queue:
                u_type = delta.get("type")
                data = delta.get("data", {})
                
                if u_type == "fact":
                    self.memory.set_fact(data.get("key"), data.get("value"), data.get("category", "user_preference"))
                elif u_type == "dialogue":
                    self.memory.record_dialogue(data.get("role"), data.get("content"), data.get("session_id", "synced"))
                synced_count += 1

            self.offline_queue.clear()
            logger.info(f"[NETWORK ROUTER] Successfully merged {synced_count} offline updates!")
        return synced_count
