from django.core.management.base import BaseCommand
from api.utils import load_mock_data

class Command(BaseCommand):
    help = 'Load mock data from filesystem into database'

    def handle(self, *args, **options):
        self.stdout.write('Loading mock data...')
        load_mock_data()
        self.stdout.write(self.style.SUCCESS('Successfully loaded mock data'))
