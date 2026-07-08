from django.core.management.base import BaseCommand

from charlie_app.ml_service import train_and_save_model


class Command(BaseCommand):
    help = 'Train and save a pretrained report-category classifier'

    def handle(self, *args, **options):
        model_path = train_and_save_model(force=True)
        self.stdout.write(self.style.SUCCESS(f'Pretrained classifier saved to {model_path}'))
