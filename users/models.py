from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.email

class Newsletter(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)
    
    def __str__(self):
        return self.subject

class Contact(models.Model):
    INQUIRY_TYPE_CHOICES = (
        ('general', 'General Inquiry'),
        ('feedback', 'Feedback'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('destination', 'Destination Comment'),
        ('activity', 'Activity Comment'),
        ('event', 'Event Comment'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    reference_id = models.PositiveIntegerField(null=True, blank=True, help_text='ID of the item being commented on, if applicable')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name}: {self.subject}"
    
    class Meta:
        ordering = ['-created_at']
