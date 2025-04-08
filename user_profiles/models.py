from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profiles_profile')
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    education = models.CharField(max_length=100, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def save(self, *args, **kwargs):
        # Create default image if it doesn't exist
        if not self.image:
            self.image = 'default.jpg'
        super().save(*args, **kwargs)

# Signal to create profile when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Try to get the profile, create if it doesn't exist
    try:
        profile = Profile.objects.get(user=instance)
        profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.profile.user.username}'s profile"
    
class ProfileComment(models.Model):
    profile_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_comments_received')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_comments_made')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.profile_user.username}'s profile"
    
    class Meta:
        ordering = ['-created_at']

   
