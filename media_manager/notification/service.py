from media_manager.notification.repository import NotificationRepository
from media_manager.notification.schemas import NotificationId, Notification
from media_manager.notification.manager import notification_manager


class NotificationService:
    def __init__(
        self,
        notification_repository: NotificationRepository,
    ):
        self.notification_repository = notification_repository
        self.notification_manager = notification_manager

    def get_notification(self, id: NotificationId) -> Notification:
        return self.notification_repository.get_notification(id=id)

    def get_unread_notifications(self) -> list[Notification]:
        return self.notification_repository.get_unread_notifications()

    def get_all_notifications(self) -> list[Notification]:
        return self.notification_repository.get_all_notifications()

    def save_notification(self, notification: Notification) -> None:
        return self.notification_repository.save_notification(notification)

    def mark_notification_as_read(self, id: NotificationId) -> None:
        return self.notification_repository.mark_notification_as_read(id=id)

    def mark_notification_as_unread(self, id: NotificationId) -> None:
        return self.notification_repository.mark_notification_as_unread(id=id)

    def delete_notification(self, id: NotificationId) -> None:
        return self.notification_repository.delete_notification(id=id)

    def send_notification_to_all_providers(self, title: str, message: str) -> None:
        self.notification_manager.send_notification(title, message)

        internal_notification = Notification(message=f"{title}: {message}", read=False)
        self.save_notification(internal_notification)
        return
