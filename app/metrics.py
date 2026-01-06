# app/metrics.py
"""
Simple metrics collection for observability.
Tracks WebSocket connections and message counts.
"""
import time
from typing import Dict
from collections import deque
from threading import Lock

class Metrics:
    """Simple in-memory metrics collector."""

    def __init__(self):
        self.lock = Lock()
        # Counters
        self.websocket_connections_total = 0
        self.messages_sent_total = 0

        # Message rate tracking (last 60 seconds)
        self.message_timestamps = deque(maxlen=1000)  # Store timestamps of last 1000 messages

    def increment_websocket_connection(self):
        """Increment total WebSocket connections counter."""
        with self.lock:
            self.websocket_connections_total += 1

    def increment_message_sent(self):
        """Increment message counter and record timestamp."""
        with self.lock:
            self.messages_sent_total += 1
            self.message_timestamps.append(time.time())

    def get_active_connections(self, connection_manager) -> int:
        """Get current number of active WebSocket connections."""
        return sum(len(connections) for connections in connection_manager.active.values())

    def get_messages_per_second(self) -> float:
        """Calculate messages per second over the last 60 seconds."""
        with self.lock:
            now = time.time()
            # Count messages in last 60 seconds
            recent_messages = sum(1 for ts in self.message_timestamps if now - ts <= 60)
            return recent_messages / 60.0 if recent_messages > 0 else 0.0

    def get_metrics_prometheus(self, connection_manager) -> str:
        """
        Generate Prometheus-formatted metrics.

        Returns:
            String in Prometheus text format
        """
        active_connections = self.get_active_connections(connection_manager)
        messages_per_sec = self.get_messages_per_second()

        metrics = []
        metrics.append(f"# HELP pneumatic_websocket_connections_total Total number of WebSocket connections established")
        metrics.append(f"# TYPE pneumatic_websocket_connections_total counter")
        metrics.append(f"pneumatic_websocket_connections_total {self.websocket_connections_total}")

        metrics.append(f"# HELP pneumatic_websocket_connections_active Current number of active WebSocket connections")
        metrics.append(f"# TYPE pneumatic_websocket_connections_active gauge")
        metrics.append(f"pneumatic_websocket_connections_active {active_connections}")

        metrics.append(f"# HELP pneumatic_messages_sent_total Total number of messages sent")
        metrics.append(f"# TYPE pneumatic_messages_sent_total counter")
        metrics.append(f"pneumatic_messages_sent_total {self.messages_sent_total}")

        metrics.append(f"# HELP pneumatic_messages_per_second Average messages per second over last 60 seconds")
        metrics.append(f"# TYPE pneumatic_messages_per_second gauge")
        metrics.append(f"pneumatic_messages_per_second {messages_per_sec:.2f}")

        return "\n".join(metrics) + "\n"

# Global metrics instance
metrics = Metrics()
