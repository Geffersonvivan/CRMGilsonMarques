import os
from django.core.management.base import BaseCommand
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Create admin superuser from environment variables or defaults'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USER', 'gvivan')
        password = os.getenv('ADMIN_PASS', 'gvgv@2020X')

        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(f'User "{username}" already exists, skipping.')
            return

        user = Usuario.objects.create_superuser(
            username=username,
            password=password,
            perfil='admin',
            first_name='Gefferson',
            last_name='Vivan',
        )
        self.stdout.write(self.style.SUCCESS(f'Admin "{username}" created successfully.'))
