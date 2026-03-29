from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Load initial data'

    def handle(self, *args, **kwargs):
        call_command('loaddata', 'store_backup.json')
        self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))