"""
Module: backend.os.adapters.windows.notifications
Responsibility: Concrete implementation of NotificationPort for Windows.
"""
from ...ports.notification_port import NotificationPort
class WindowsNotificationAdapter(NotificationPort):
    def send_notification(self, title: str, text: str) -> bool:
        pass
