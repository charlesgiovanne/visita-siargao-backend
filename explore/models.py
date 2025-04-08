from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'

class Destination(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='destinations/')
    categories = models.ManyToManyField(Category, related_name='destinations')
    short_description = models.TextField()
    long_description = models.TextField()
    location_name = models.CharField(max_length=200, blank=True, null=True, help_text="Physical location name, different from map link")
    maps_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Activity(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='activities/')
    short_description = models.TextField()
    long_description = models.TextField()
    tips = models.TextField()
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="Approximate duration of the activity (e.g., '2-3 hours', 'Half day')")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = 'Activities'

class Culture(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='culture/')
    short_description = models.TextField()
    long_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Favorite(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='favorites')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_by')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_by')
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        item = self.destination or self.activity or self.culture
        return f"{self.user.username} - {item}"
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(destination__isnull=False) | 
                      models.Q(activity__isnull=False) | 
                      models.Q(culture__isnull=False),
                name='favorite_has_item'
            ),
            models.UniqueConstraint(
                fields=['user', 'destination'],
                name='unique_user_destination',
                condition=models.Q(destination__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['user', 'activity'],
                name='unique_user_activity',
                condition=models.Q(activity__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['user', 'culture'],
                name='unique_user_culture',
                condition=models.Q(culture__isnull=False)
            ),
        ]
