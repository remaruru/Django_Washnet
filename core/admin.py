from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, EmployeeProfile, Service, Product, Order, OrderItem, Appointment

# ─────────────────────────────────────────────
#  Site Branding
# ─────────────────────────────────────────────
admin.site.site_header  = "🧺 Washnet Administration"
admin.site.site_title   = "Washnet Admin"
admin.site.index_title  = "Welcome to the Washnet Admin Panel"


# ─────────────────────────────────────────────
#  Inlines
# ─────────────────────────────────────────────
class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name_plural = "Employee Profile"
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_total_display',)
    fields = ('item_type', 'load_index', 'service', 'product', 'quantity', 'price', 'notes', 'get_total_display')

    def get_total_display(self, obj):
        if obj.pk:
            return f"₱{obj.get_total:,.2f}"
        return "—"
    get_total_display.short_description = "Line Total"


# ─────────────────────────────────────────────
#  User Admin
# ─────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeProfileInline,)

    list_display  = ('username', 'full_name', 'role_badge', 'email', 'phone_number', 'is_active', 'is_staff', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering      = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address', 'delivery_notes')}),
        (_('Role'), {'fields': ('role',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'), 'classes': ('collapse',)}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )

    def full_name(self, obj):
        name = obj.get_full_name()
        return name if name else "—"
    full_name.short_description = "Full Name"

    def role_badge(self, obj):
        colors = {
            'ADMIN':    '#c0392b',
            'EMPLOYEE': '#2980b9',
            'CUSTOMER': '#27ae60',
            'RIDER':    '#8e44ad',
        }
        color = colors.get(obj.role, '#7f8c8d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = "Role"


# ─────────────────────────────────────────────
#  Employee Profile Admin
# ─────────────────────────────────────────────
@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'orders_processed')
    search_fields = ('user__username', 'user__email')
    ordering      = ('-orders_processed',)


# ─────────────────────────────────────────────
#  Service Admin
# ─────────────────────────────────────────────
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ('name', 'price_display', 'is_active', 'description', 'active_badge')
    list_filter   = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)   # toggle active right from the list

    def price_display(self, obj):
        return f"₱{obj.price:,.2f}"
    price_display.short_description = "Price"

    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#27ae60;font-weight:bold">{}</span>', '✔ Active')
        return format_html('<span style="color:#c0392b;font-weight:bold">{}</span>', '✘ Inactive')
    active_badge.short_description = "Status"


# ─────────────────────────────────────────────
#  Product Admin
# ─────────────────────────────────────────────
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('name', 'price_display', 'stock', 'stock_status', 'description')
    search_fields = ('name',)
    ordering      = ('name',)

    def price_display(self, obj):
        return f"₱{obj.price:,.2f}"
    price_display.short_description = "Price"

    def stock_status(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="color:#c0392b;font-weight:bold">{}</span>', 'Out of Stock')
        elif obj.stock <= 10:
            return format_html('<span style="color:#e67e22;font-weight:bold">Low ({})</span>', obj.stock)
        return format_html('<span style="color:#27ae60;font-weight:bold">{}</span>', 'OK')
    stock_status.short_description = "Stock Level"


# ─────────────────────────────────────────────
#  Order Admin
# ─────────────────────────────────────────────
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines       = (OrderItemInline,)
    list_display  = ('id', 'customer_display', 'order_type', 'status_badge', 'payment_badge', 'release_method', 'total_display', 'rider', 'created_at')
    list_filter   = ('status', 'order_type', 'payment_status', 'payment_method', 'release_method', 'created_at')
    search_fields = ('id', 'customer__username', 'walkin_name', 'receipt_token', 'delivery_address')
    ordering      = ('-created_at',)
    readonly_fields = ('receipt_token', 'created_at', 'updated_at', 'qr_code')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Order Info', {
            'fields': ('order_type', 'status', 'receipt_token', 'created_at', 'updated_at')
        }),
        ('Customer', {
            'fields': ('customer', 'walkin_name', 'employee')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'payment_reference', 'total_amount')
        }),
        ('Delivery / Release', {
            'fields': ('release_method', 'rider', 'delivery_address', 'delivery_contact', 'delivery_notes', 'scheduled_pickup')
        }),
        ('QR Code', {
            'fields': ('qr_code',),
            'classes': ('collapse',),
        }),
    )

    def customer_display(self, obj):
        if obj.customer:
            return obj.customer.username
        return obj.walkin_name or "Walk-in"
    customer_display.short_description = "Customer"

    def total_display(self, obj):
        return f"₱{obj.total_amount:,.2f}"
    total_display.short_description = "Total"

    STATUS_COLORS = {
        'EXPECTING_DROP_OFF':   '#3498db',
        'PENDING_ACCEPTANCE':   '#e67e22',
        'RIDER_ACCEPTED':       '#9b59b6',
        'PICKED_UP':            '#1abc9c',
        'AT_SHOP':              '#2ecc71',
        'PROCESSING':           '#f39c12',
        'READY_FOR_DELIVERY':   '#27ae60',
        'OUT_FOR_DELIVERY':     '#8e44ad',
        'COMPLETED':            '#2c3e50',
        'CANCELLED':            '#c0392b',
    }

    def status_badge(self, obj):
        color = self.STATUS_COLORS.get(obj.status, '#7f8c8d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;white-space:nowrap">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def payment_badge(self, obj):
        if obj.payment_status == 'PAID':
            return format_html('<span style="color:#27ae60;font-weight:bold">{}</span>', '✔ Paid')
        return format_html('<span style="color:#c0392b;font-weight:bold">{}</span>', '✘ Unpaid')
    payment_badge.short_description = "Payment"


# ─────────────────────────────────────────────
#  OrderItem Admin (standalone)
# ─────────────────────────────────────────────
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'order', 'item_type', 'quantity', 'price_display', 'line_total')
    list_filter   = ('item_type',)
    search_fields = ('order__id', 'service__name', 'product__name')
    ordering      = ('-order__created_at',)

    def price_display(self, obj):
        return f"₱{obj.price:,.2f}"
    price_display.short_description = "Unit Price"

    def line_total(self, obj):
        return f"₱{obj.get_total:,.2f}"
    line_total.short_description = "Line Total"


# ─────────────────────────────────────────────
#  Appointment Admin
# ─────────────────────────────────────────────
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'customer', 'appointment_type', 'appointment_date', 'status_badge', 'resulting_order', 'created_at')
    list_filter   = ('appointment_type', 'status', 'appointment_date')
    search_fields = ('customer__username', 'notes')
    ordering      = ('-appointment_date',)
    date_hierarchy = 'appointment_date'

    APPT_STATUS_COLORS = {
        'PENDING':   '#e67e22',
        'CONFIRMED': '#2980b9',
        'COMPLETED': '#27ae60',
        'CANCELLED': '#c0392b',
    }

    def status_badge(self, obj):
        color = self.APPT_STATUS_COLORS.get(obj.status, '#7f8c8d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"
