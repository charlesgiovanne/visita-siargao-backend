from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, get_connection
from users.models import Newsletter, Subscriber
import sys

class Command(BaseCommand):
    help = 'Send a newsletter to all active subscribers'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, help='ID of an existing newsletter to send')
        parser.add_argument('--subject', type=str, help='Subject of the newsletter')
        parser.add_argument('--content', type=str, help='HTML content of the newsletter')
        parser.add_argument('--list', action='store_true', help='List all newsletters')
        parser.add_argument('--subscribers', action='store_true', help='List all active subscribers')

    def handle(self, *args, **options):
        # List all newsletters
        if options['list']:
            newsletters = Newsletter.objects.all().order_by('-created_at')
            if not newsletters.exists():
                self.stdout.write(self.style.WARNING('No newsletters found'))
                return
            
            self.stdout.write(self.style.SUCCESS('Available newsletters:'))
            for newsletter in newsletters:
                status = 'SENT' if newsletter.sent else 'DRAFT'
                sent_info = f" (Sent on: {newsletter.sent_at.strftime('%Y-%m-%d %H:%M')})" if newsletter.sent else ""
                self.stdout.write(f"ID: {newsletter.id} | {status}{sent_info} | Subject: {newsletter.subject}")
            return

        # List all active subscribers
        if options['subscribers']:
            active_subscribers = Subscriber.objects.filter(is_active=True)
            inactive_subscribers = Subscriber.objects.filter(is_active=False)
            
            self.stdout.write(self.style.SUCCESS(f'Active subscribers: {active_subscribers.count()}'))
            for subscriber in active_subscribers:
                self.stdout.write(f"- {subscriber.email} (Subscribed: {subscriber.subscribed_at.strftime('%Y-%m-%d')})")
            
            self.stdout.write(self.style.WARNING(f'\nInactive subscribers: {inactive_subscribers.count()}'))
            return

        # Send an existing newsletter
        if options['id']:
            try:
                newsletter = Newsletter.objects.get(id=options['id'])
            except Newsletter.DoesNotExist:
                raise CommandError(f'Newsletter with ID {options["id"]} does not exist')
            
            if newsletter.sent:
                self.stdout.write(self.style.WARNING(f'Newsletter "{newsletter.subject}" has already been sent on {newsletter.sent_at}'))
                if not self.confirm_action('Do you want to send it again?'):
                    return
        
        # Create and send a new newsletter
        elif options['subject'] and options['content']:
            newsletter = Newsletter(
                subject=options['subject'],
                content=options['content']
            )
            newsletter.save()
            self.stdout.write(self.style.SUCCESS(f'Created new newsletter: "{newsletter.subject}"'))
        else:
            self.stdout.write(self.style.ERROR('You must provide either an ID of an existing newsletter or both subject and content for a new one'))
            return
        
        # Get all active subscribers
        active_subscribers = Subscriber.objects.filter(is_active=True)
        
        if not active_subscribers.exists():
            self.stdout.write(self.style.ERROR('No active subscribers found'))
            return
        
        if not self.confirm_action(f'Send newsletter "{newsletter.subject}" to {active_subscribers.count()} active subscribers?'):
            return
        
        # Prepare email data
        subject = newsletter.subject
        from_email = 'noreply@siargao.com'
        html_message = newsletter.content
        plain_message = strip_tags(html_message)
        
        # Send emails in batches
        batch_size = 50
        total_subscribers = active_subscribers.count()
        success_count = 0
        failed_emails = []
        
        # Process subscribers in batches
        subscriber_batches = [active_subscribers[i:i+batch_size] for i in range(0, total_subscribers, batch_size)]
        
        with self.stdout.progressbar(subscriber_batches, prefix='Sending emails: ') as progress_bar:
            for batch in progress_bar:
                # Create a mass email
                messages = []
                for subscriber in batch:
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=plain_message,
                        from_email=from_email,
                        to=[subscriber.email],
                    )
                    email.attach_alternative(html_message, "text/html")
                    messages.append(email)
                
                # Send all emails in this batch
                try:
                    connection = get_connection()
                    connection.open()
                    connection.send_messages(messages)
                    connection.close()
                    success_count += len(batch)
                except Exception as e:
                    # If batch sending fails, try sending individually
                    for i, subscriber in enumerate(batch):
                        try:
                            messages[i].send()
                            success_count += 1
                        except Exception as e:
                            failed_emails.append({
                                'email': subscriber.email,
                                'error': str(e)
                            })
        
        # Mark the newsletter as sent
        if success_count > 0:
            newsletter.sent = True
            newsletter.sent_at = timezone.now()
            newsletter.save()
        
        # Print results
        self.stdout.write(self.style.SUCCESS(f'\nNewsletter sent to {success_count} out of {total_subscribers} active subscribers'))
        
        if failed_emails:
            self.stdout.write(self.style.WARNING('\nFailed to send to the following emails:'))
            for failure in failed_emails:
                self.stdout.write(f"- {failure['email']}: {failure['error']}")
    
    def confirm_action(self, message):
        """Ask for confirmation before proceeding"""
        self.stdout.write(f"\n{message} (y/n) ")
        response = input().lower()
        return response in ['y', 'yes']
