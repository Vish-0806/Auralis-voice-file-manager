"""
Module: backend.os.adapters.linux.notifications
Responsibility: Concrete implementation of NotificationPort for Linux.
"""
from os.ports.notification_port import NotificationPort
class LinuxNotificationAdapter(NotificationPort):
    def send_notification(self, title: str, text: str) -> bool:
        pass
