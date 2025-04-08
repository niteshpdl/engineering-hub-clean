from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from user_profiles.models import Profile

class Command(BaseCommand):
    help = 'Creates missing user profiles'

    def handle(self, *args, **options):
        users_without_profiles = []
        
        for user in User.objects.all():
            # Check if profile exists without directly accessing user.profile
            if not Profile.objects.filter(user=user).exists():
                users_without_profiles.append(user.username)
                Profile.objects.create(user=user)
        
        if users_without_profiles:
            self.stdout.write(self.style.SUCCESS(f'Created profiles for: {", ".join(users_without_profiles)}'))
        else:
            self.stdout.write(self.style.SUCCESS('No missing profiles found'))
