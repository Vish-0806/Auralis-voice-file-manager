"""
Module: backend.os.ports.notification_port
Responsibility: Abstract port interface defining OS tray alert dispatch actions.
"""
from abc import ABC, abstractmethod
class NotificationPort(ABC):
    @abstractmethod
    def send_notification(self, title: str, text: str) -> bool:
        pass
