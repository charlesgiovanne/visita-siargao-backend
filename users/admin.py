from django.contrib import admin
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib import messages
from .models import Subscriber, Newsletter, Contact

# Register your models here.

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email',)
    actions = ['reactivate_subscribers']
    
    def reactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} subscribers were successfully reactivated.")
    reactivate_subscribers.short_description = "Reactivate selected subscribers"

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'sent_at', 'sent')
    list_filter = ('sent',)
    search_fields = ('subject', 'content')
    readonly_fields = ('sent_at', 'sent')
    fields = ('subject', 'content', 'sent', 'sent_at')
    actions = ['send_newsletter']
    
    def send_newsletter(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one newsletter to send at a time.", level=messages.ERROR)
            return
            
        newsletter = queryset.first()
        
        if newsletter.sent:
            self.message_user(request, f"Newsletter '{newsletter.subject}' has already been sent on {newsletter.sent_at}.", level=messages.WARNING)
            return
        
        # Get all active subscribers
        active_subscribers = Subscriber.objects.filter(is_active=True)
        
        if not active_subscribers.exists():
            self.message_user(request, "No active subscribers found. Newsletter not sent.", level=messages.ERROR)
            return
        
        # Prepare email data
        subject = newsletter.subject
        from_email = 'noreply@siargao.com'
        html_message = newsletter.content
        plain_message = strip_tags(html_message)
        
        # Send emails in batches for efficiency
        batch_size = 50  # Send emails in batches of 50 recipients
        total_subscribers = active_subscribers.count()
        success_count = 0
        failed_emails = []
        
        # Process subscribers in batches
        subscriber_batches = [active_subscribers[i:i+batch_size] for i in range(0, total_subscribers, batch_size)]
        
        for batch in subscriber_batches:
            # For each batch, create a mass email
            messages_to_send = []
            for subscriber in batch:
                # Create an email message with both HTML and plain text versions
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=from_email,
                    to=[subscriber.email],
                )
                email.attach_alternative(html_message, "text/html")
                messages_to_send.append(email)
            
            # Send all emails in this batch
            try:
                # Use connection to send all emails in one connection
                connection = get_connection()
                connection.open()
                connection.send_messages(messages_to_send)
                connection.close()
                success_count += len(batch)
            except Exception as e:
                # If batch sending fails, try sending individually to identify which emails failed
                for i, subscriber in enumerate(batch):
                    try:
                        messages_to_send[i].send()
                        success_count += 1
                    except Exception as e:
                        failed_emails.append({
                            'email': subscriber.email,
                            'error': str(e)
                        })
        
        # Mark the newsletter as sent if at least one email was successfully sent
        if success_count > 0:
            newsletter.sent = True
            newsletter.sent_at = timezone.now()
            newsletter.save()
            
            success_message = f"Newsletter sent to {success_count} out of {total_subscribers} active subscribers."
            if failed_emails:
                failed_list = ', '.join([f['email'] for f in failed_emails[:5]])
                if len(failed_emails) > 5:
                    failed_list += f" and {len(failed_emails) - 5} more"
                success_message += f" Failed to send to: {failed_list}"
                
            self.message_user(request, success_message)
        else:
            self.message_user(request, "Failed to send the newsletter. Please check your email configuration.", level=messages.ERROR)
    
    send_newsletter.short_description = "Send newsletter to all active subscribers"

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'inquiry_type', 'subject', 'created_at', 'is_read')
    list_filter = ('inquiry_type', 'is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    fields = ('name', 'email', 'inquiry_type', 'subject', 'message', 'reference_id', 'is_read', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"
