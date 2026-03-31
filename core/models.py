from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import string
from django.utils.crypto import get_random_string

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

    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customer_orders')
    walkin_name = models.CharField(max_length=100, blank=True, null=True)
    employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_orders') # The one who created via POS
    rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    
    order_type = models.CharField(max_length=20, choices=OrderTypeChoices.choices, default=OrderTypeChoices.WALK_IN)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING_ACCEPTANCE)
    payment_method = models.CharField(max_length=20, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.CASH)
    payment_status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.UNPAID)
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. GCash Ref No.")
    
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
        return self.quantity * self.price

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
