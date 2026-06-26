"""
Module: backend.os.adapters.macos.notifications
Responsibility: Concrete implementation of NotificationPort for Macos.
"""
from os.ports.notification_port import NotificationPort
class MacosNotificationAdapter(NotificationPort):
    def send_notification(self, title: str, text: str) -> bool:
        pass
