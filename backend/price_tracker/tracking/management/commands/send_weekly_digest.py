"""Management command для отправки еженедельной сводки по ценам."""
from django.core.management.base import BaseCommand

from tracking.notifications import send_weekly_digest


class Command(BaseCommand):
    help = "Отправить еженедельную email-сводку всем подписанным пользователям."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Отправка еженедельной сводки...")
        send_weekly_digest()
        self.stdout.write(self.style.SUCCESS("Готово."))
