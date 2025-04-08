from django.db import models
from django.contrib.auth.models import User
import os
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

class Department(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Semester(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='semesters')
    number = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ['department', 'number']
        ordering = ['department', 'number']
    
    def __str__(self):
        return f"{self.department.name} - Semester {self.number}"

# Update the Resource model with additional fields
class Resource(models.Model):
    thumbnail = models.ImageField(upload_to='resource_thumbnails/', blank=True, null=True)
    RESOURCE_TYPES = (
        ('notes', 'Notes'),
        ('handwritten', 'Handwritten Notes'),
        ('insight', 'Insight'),
        ('syllabus', 'Syllabus'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='resources', blank=True, null=True)
    direct_link = models.URLField(blank=True, null=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='resources')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='resources')
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='resource_thumbnails', blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, null=True)
    
    # These will be computed from the Vote model
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        return "No file"
    
    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
        
    def update_vote_counts(self):
        """Update the vote counters based on related Vote objects"""
        self.upvotes = self.votes.filter(vote_type='upvote').count()
        self.downvotes = self.votes.filter(vote_type='downvote').count()
        self.save(update_fields=['upvotes', 'downvotes'])

    def get_thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        else:
            # Return default based on resource type
            resource_type_icons = {
                'notes': 'notes.png',
                'handwritten': 'handwritten.png',
                'insight': 'insight.png',
                'syllabus': 'syllabus.png',
            }
            default_icon = resource_type_icons.get(self.resource_type, 'document.png')
            return f'/static/images/{default_icon}'
    
class Comment(models.Model):
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()  # This should be 'text', not 'content'
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.resource.title}"
    
      
class Project(models.Model):
    CATEGORY_CHOICES = [
        ('ai', 'AI Projects'),
        ('ml', 'ML Projects'),
        ('iot', 'IoT Projects'),
        ('software', 'Software Projects'),
        ('major', 'Major Projects'),
        ('minor', 'Minor Projects'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    documentation = models.FileField(upload_to='project_docs/')
    team_members = models.CharField(max_length=255, blank=True, null=True)
    supervisor = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
           
class Vote(models.Model):
    VOTE_CHOICES = (
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['resource', 'user']
        
    def __str__(self):
        return f"{self.user.username}'s {self.vote_type} on {self.resource.title}"
    

    
    
