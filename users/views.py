from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Subscriber, Newsletter, Contact
from .serializers import UserSerializer, SubscriberSerializer, NewsletterSerializer, ContactSerializer, CustomTokenObtainPairSerializer, UserProfileSerializer
from django.utils import timezone
from django.core.mail import send_mail, send_mass_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

class SubscriberViewSet(viewsets.ModelViewSet):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'unsubscribe', 'resubscribe']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            existing_subscriber = Subscriber.objects.filter(email=email).first()
            
            if existing_subscriber:
                if existing_subscriber.is_active:
                    return Response({'detail': 'Email already subscribed'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Reactivate the subscription
                    existing_subscriber.is_active = True
                    existing_subscriber.save()
                    return Response(self.get_serializer(existing_subscriber).data, status=status.HTTP_200_OK)
            
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        subscriber = Subscriber.objects.filter(email=email).first()
        if not subscriber:
            return Response({'detail': 'Email not found in our subscribers list'}, status=status.HTTP_404_NOT_FOUND)
            
        if not subscriber.is_active:
            return Response({'detail': 'This email is already unsubscribed'}, status=status.HTTP_400_BAD_REQUEST)
            
        subscriber.is_active = False
        subscriber.save()
        
        return Response({'detail': 'Successfully unsubscribed'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def resubscribe(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        subscriber = Subscriber.objects.filter(email=email).first()
        if not subscriber:
            # If no subscriber record exists, create a new one
            serializer = self.get_serializer(data={'email': email})
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        if subscriber.is_active:
            return Response({'detail': 'This email is already subscribed'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Reactivate the subscription
        subscriber.is_active = True
        subscriber.save()
        
        return Response(self.get_serializer(subscriber).data, status=status.HTTP_200_OK)

class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all().order_by('-created_at')
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        newsletter = self.get_object()
        
        if newsletter.sent:
            return Response({'detail': 'This newsletter has already been sent'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all active subscribers
        active_subscribers = Subscriber.objects.filter(is_active=True)
        
        if not active_subscribers.exists():
            return Response({'detail': 'No active subscribers found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare email data
        subject = newsletter.subject
        from_email = 'noreply@siargao.com'
        html_message = newsletter.content
        plain_message = strip_tags(html_message)
        
        # Use batch email sending for efficiency
        # This way, all emails will be sent in one batch instead of individual requests
        batch_size = 50  # Send emails in batches of 50 recipients
        total_subscribers = active_subscribers.count()
        success_count = 0
        failed_emails = []
        
        # Process subscribers in batches
        subscriber_batches = [active_subscribers[i:i+batch_size] for i in range(0, total_subscribers, batch_size)]
        
        for batch in subscriber_batches:
            # For each batch, create a mass email
            messages = []
            for subscriber in batch:
                # Create an email message with both HTML and plain text versions
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
                # Use connection to send all emails in one connection
                connection = email.connection
                connection.open()
                connection.send_messages(messages)
                connection.close()
                success_count += len(batch)
            except Exception as e:
                # If batch sending fails, try sending individually to identify which emails failed
                for i, subscriber in enumerate(batch):
                    try:
                        messages[i].send()
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
        
        return Response({
            'detail': f'Newsletter sent to {success_count} out of {total_subscribers} active subscribers',
            'success_count': success_count,
            'total_subscribers': total_subscribers,
            'failed_emails': failed_emails if failed_emails else None
        })

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all().order_by('-created_at')
    serializer_class = ContactSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Save the contact message
            contact = serializer.save()
            
            # Send notification email to admin about the new contact
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@siargao.com')
            
            # Get reference item information if applicable
            reference_info = ""
            if contact.inquiry_type in ['destination', 'activity', 'event'] and contact.reference_id:
                try:
                    if contact.inquiry_type == 'destination':
                        from explore.models import Destination
                        item = Destination.objects.get(id=contact.reference_id)
                        reference_info = f"Reference: {contact.inquiry_type.title()} - {item.title} (ID: {contact.reference_id})\n"
                    elif contact.inquiry_type == 'activity':
                        from explore.models import Activity
                        item = Activity.objects.get(id=contact.reference_id)
                        reference_info = f"Reference: {contact.inquiry_type.title()} - {item.title} (ID: {contact.reference_id})\n"
                    elif contact.inquiry_type == 'event':
                        from events.models import Event
                        item = Event.objects.get(id=contact.reference_id)
                        reference_info = f"Reference: {contact.inquiry_type.title()} - {item.title} (ID: {contact.reference_id})\n"
                except Exception:
                    # If item doesn't exist, continue without reference info
                    pass
            
            # Prepare admin notification email
            subject = f'New {contact.inquiry_type.title()} Message: {contact.subject}'
            message = f"""New message received from {contact.name} ({contact.email}):
            
Type: {dict(Contact.INQUIRY_TYPE_CHOICES).get(contact.inquiry_type, contact.inquiry_type.title())}\n
{reference_info}Subject: {contact.subject}

Message:
{contact.message}

Sent on: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}

You can view and manage all messages in the admin panel.
            """
            
            try:
                # Send email notification to admin
                send_mail(
                    subject=subject,
                    message=message,
                    from_email='noreply@siargao.com',
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
            except Exception as e:
                # Continue even if admin notification fails
                pass
            
            # Send confirmation email to the user
            try:
                user_subject = 'Thank you for contacting Siargao Tourism'
                user_message = f"""Dear {contact.name},

Thank you for your {contact.inquiry_type.replace('_', ' ')} message to Siargao Tourism. We have received your message and will get back to you shortly.

Your message details:
Subject: {contact.subject}

We appreciate your interest in Siargao Island and will respond as soon as possible.

Sincerely,
Siargao Tourism Team
                """
                
                send_mail(
                    subject=user_subject,
                    message=user_message,
                    from_email='noreply@siargao.com',
                    recipient_list=[contact.email],
                    fail_silently=True,
                )
            except Exception as e:
                # Continue even if user confirmation fails
                pass
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        contact = self.get_object()
        contact.is_read = True
        contact.save()
        return Response({'detail': 'Contact marked as read'}, status=status.HTTP_200_OK)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
