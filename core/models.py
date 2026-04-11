from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import string
import hashlib
import secrets
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

def generate_receipt_token():
    return get_random_string(12, allowed_chars=string.ascii_letters + string.digits)

class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        EMPLOYEE = 'EMPLOYEE', _('Employee')
        CUSTOMER = 'CUSTOMER', _('Customer')
        RIDER = 'RIDER', _('Rider')

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.CUSTOMER,
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    delivery_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    orders_processed = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Employee Profile - {self.user.username}"

class Service(models.Model):
    name = models.CharField(max_length=100) # e.g. Wash, Dry, Fold, Wash & Fold
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100) # e.g. Zonrox, Fabric Conditioner
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    class StatusChoices(models.TextChoices):
        EXPECTING_DROP_OFF = 'EXPECTING_DROP_OFF', _('Awaiting Customer Drop-Off')
        PENDING_ACCEPTANCE = 'PENDING_ACCEPTANCE', _('Waiting for Rider')
        RIDER_ACCEPTED = 'RIDER_ACCEPTED', _('Rider on the Way to Pick Up')
        PICKED_UP = 'PICKED_UP', _('Picked Up')
        AT_SHOP = 'AT_SHOP', _('At the Shop (Waiting for Processing)')
        PROCESSING = 'PROCESSING', _('Washing / Processing')
        READY_FOR_DELIVERY = 'READY_FOR_DELIVERY', _('Ready for Delivery')
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', _('Out for Delivery')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class PaymentMethodChoices(models.TextChoices):
        CASH = 'CASH', _('Cash')
        GCASH = 'GCASH', _('GCash')
        PAYPAL = 'PAYPAL', _('PayPal')

    class PaymentStatusChoices(models.TextChoices):
        UNPAID = 'UNPAID', _('Unpaid')
        PAID = 'PAID', _('Paid')

    class OrderTypeChoices(models.TextChoices):
        WALK_IN = 'WALK_IN', _('Walk-In')
        DELIVERY = 'DELIVERY', _('Delivery')
        APPOINTMENT = 'APPOINTMENT', _('Appointment')
        DROP_OFF = 'DROP_OFF', _('Self Drop-Off')

    class ReleaseMethodChoices(models.TextChoices):
        PICKUP = 'PICKUP', _('Customer Pickup')
        DELIVERY = 'DELIVERY', _('Deliver to Customer')

    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customer_orders')
    walkin_name = models.CharField(max_length=100, blank=True, null=True)
    employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_orders') # The one who created via POS
    rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    
    order_type = models.CharField(max_length=20, choices=OrderTypeChoices.choices, default=OrderTypeChoices.WALK_IN)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING_ACCEPTANCE)
    payment_method = models.CharField(max_length=20, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.CASH)
    payment_status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.UNPAID)
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. GCash Ref No.")
    
    release_method = models.CharField(max_length=20, choices=ReleaseMethodChoices.choices, default=ReleaseMethodChoices.PICKUP)
    delivery_address = models.TextField(blank=True, null=True)
    delivery_contact = models.CharField(max_length=20, blank=True, null=True)
    delivery_notes = models.TextField(blank=True, null=True)
    
    receipt_token = models.CharField(max_length=12, default=generate_receipt_token, unique=True, editable=False)
    
    # Shopee-like delivery metadata
    scheduled_pickup = models.DateTimeField(null=True, blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} - {self.get_status_display()}"

    @property
    def status_choices_list(self):
        return self.StatusChoices.choices

    def save(self, *args, **kwargs):
        # Auto-inherit from customer profile if not provided
        if self.customer:
            if not self.delivery_address and self.customer.address:
                self.delivery_address = self.customer.address
            if not self.delivery_contact and self.customer.phone_number:
                self.delivery_contact = self.customer.phone_number
            if not self.delivery_notes and self.customer.delivery_notes:
                self.delivery_notes = self.customer.delivery_notes
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    class ItemTypeChoices(models.TextChoices):
        SERVICE = 'SERVICE', _('Service')
        ADDON = 'ADDON', _('Addon')
        PRODUCT = 'PRODUCT', _('Product')
        
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=10, choices=ItemTypeChoices.choices, default=ItemTypeChoices.SERVICE)
    load_index = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=5, decimal_places=2) # Weight in kg for services, pieces for products
    price = models.DecimalField(max_digits=10, decimal_places=2) # Snapshot of price at time of order

    @property
    def get_total(self):
        from decimal import Decimal
        return (self.quantity * self.price).quantize(Decimal('0.01'))

    def __str__(self):
        item_name = self.service.name if self.service else (self.product.name if self.product else "Item")
        load_inf = f" (Load {self.load_index})" if self.load_index else ""
        return f"[{self.get_item_type_display()}]{load_inf} {self.quantity} x {item_name} for Order #{self.order.id}"

class Appointment(models.Model):
    class TypeChoices(models.TextChoices):
        PICKUP = 'PICKUP', _('Pick Up')
        DELIVERY = 'DELIVERY', _('Delivery')
        
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=10, choices=TypeChoices.choices, default=TypeChoices.PICKUP)
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    notes = models.TextField(blank=True, null=True)
    
    # Link to resulting order if this appointment was picked up
    resulting_order = models.OneToOneField('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='originating_appointment')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_appointment_type_display()} Appointment for {self.customer.username} on {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"


# ── Admin OTP Security ────────────────────────────────────────────────────────

class AdminOTPEmail(models.Model):
    """Stores the dedicated OTP email address for an Admin account."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_otp_email',
        limit_choices_to={'role': 'ADMIN'},
    )
    otp_email = models.EmailField(
        help_text="Email address where Admin OTP codes are delivered."
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OTP Email for {self.user.username}: {self.otp_email}"

    @staticmethod
    def get_for_user(user):
        """Return the OTP email address for the admin, or fall back to user.email."""
        try:
            return user.admin_otp_email.otp_email
        except AdminOTPEmail.DoesNotExist:
            return user.email


class AdminOTP(models.Model):
    """Stores a single hashed OTP token for admin authentication events."""

    class PurposeChoices(models.TextChoices):
        LOGIN = 'LOGIN', _('Login Verification')
        EMAIL_CHANGE = 'EMAIL_CHANGE', _('Email Change Verification')

    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 5
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_otps',
    )
    hashed_code = models.CharField(max_length=64)   # SHA-256 hex digest
    purpose = models.CharField(
        max_length=20,
        choices=PurposeChoices.choices,
        default=PurposeChoices.LOGIN,
    )
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP [{self.purpose}] for {self.user.username} — {'used' if self.is_used else 'pending'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_locked(self):
        return self.attempts >= self.MAX_ATTEMPTS

    @classmethod
    def generate(cls, user, purpose):
        """
        Invalidate all existing active OTPs for this user+purpose,
        generate a new 6-digit plain code, store its SHA-256 hash, and
        return (otp_instance, plain_code) so the plain code can be emailed.
        """
        # Invalidate previous active OTPs for same purpose
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

        plain_code = ''.join(secrets.choice('0123456789') for _ in range(6))
        hashed = hashlib.sha256(plain_code.encode()).hexdigest()
        otp = cls.objects.create(
            user=user,
            hashed_code=hashed,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES),
        )
        return otp, plain_code

    def verify(self, submitted_code):
        """
        Attempt to verify a submitted plain code.
        Returns True on success, False otherwise.
        Marks OTP as used on success; increments attempt counter on failure.
        """
        if self.is_used or self.is_expired or self.is_locked:
            return False
        submitted_hash = hashlib.sha256(submitted_code.encode()).hexdigest()
        if secrets.compare_digest(submitted_hash, self.hashed_code):
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True
        self.attempts += 1
        self.save(update_fields=['attempts'])
        return False

    @classmethod
    def get_active(cls, user, purpose):
        """Return the most recent non-expired, non-used OTP for this user+purpose."""
        return cls.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).first()
