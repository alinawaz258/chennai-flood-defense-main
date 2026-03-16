from __future__ import annotations

from datetime import datetime
from typing import Dict, List


class AlertSystemService:
    """Dispatches citizen alerts over SMS/WhatsApp/Push channels (mocked sinks)."""

    SUPPORTED_CHANNELS = {"sms", "whatsapp", "push"}

    def send_alert(self, message: str, channels: List[str], recipients: List[str]) -> Dict[str, object]:
        used = [c.lower() for c in channels if c.lower() in self.SUPPORTED_CHANNELS]
        events = [
            {
                "channel": channel,
                "recipient": recipient,
                "status": "queued",
                "timestamp": datetime.utcnow().isoformat(),
            }
            for channel in used
            for recipient in recipients
        ]
        return {
            "message": message,
            "channels": used,
            "total_recipients": len(recipients),
            "events": events,
        }
