from django.db import models

# Create your models here.

class Event(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/')
    description = models.TextField()
    date = models.DateField()
    month = models.CharField(max_length=20)  # To easily filter events by month
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-populate the month field based on the date
        if self.date:
            self.month = self.date.strftime('%B')
        super().save(*args, **kwargs)
