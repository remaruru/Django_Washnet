from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib import messages # type: ignore
from django.utils import timezone # type: ignore
from django.db.models import Sum, Count, Q, F # type: ignore
from django.db.models.functions import TruncDay, TruncMonth # type: ignore
from django.urls import reverse # type: ignore
import json
import qrcode # type: ignore
from io import BytesIO
from django.core.files.base import ContentFile # type: ignore
from core.models import User, Order, Appointment, Service, Product, OrderItem # type: ignore
from core.forms import CustomUserCreationForm # type: ignore

# --- AUTHENTICATION VIEWS ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_customer_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'core/register.html')
            
        user = User.objects.create_user(
            username=username, 
            password=password, 
            email=email,
            role=User.RoleChoices.CUSTOMER,
            phone_number=phone_number,
            address=address
        )
        login(request, user)
        return redirect('dashboard')
        
    return render(request, 'core/register.html')

# --- PUBLIC VIEWS ---

def home(request):
    """
    Public landing page with a 7-day forecast for the best time to do laundry.
    (This uses placeholder values until the real API is connected).
    """
    import random
    from datetime import timedelta
    
    today = timezone.now().date()
    forecast = []
    
    # Placeholder API logic: randomly assign a "rating" out of 100% and a text condition
    conditions = ['Excellent (Sunny & Dry)', 'Good (Partly Cloudy)', 'Fair (Humid)', 'Poor (Rain Expected)', 'Terrible (Stormy)']
    
    for i in range(7):
        target_date = today + timedelta(days=i)
        
        # We pseudo-randomize based on the day to keep it consistent on reload for the demo
        seed = int(target_date.strftime('%Y%m%d'))
        random.seed(seed)
        
        score = random.randint(40, 98)
        if score >= 85:
            cond = conditions[0]
            color = 'var(--secondary)' # Green
        elif score >= 70:
            cond = conditions[1]
            color = '#3B82F6' # Blue
        elif score >= 55:
            cond = conditions[2]
            color = '#F59E0B' # Orange
        else:
            cond = random.choice([conditions[3], conditions[4]])
            color = 'var(--error)' # Red
            
        forecast.append({
            'date': target_date,
            'day_name': 'Today' if i == 0 else 'Tomorrow' if i == 1 else target_date.strftime('%A'),
            'score': score,
            'condition': cond,
            'color': color
        })
        
    return render(request, 'core/home.html', {'forecast': forecast})

# --- DASHBOARD REDIRECTOR ---

@login_required
def dashboard_redirect(request):
    if request.user.role == User.RoleChoices.ADMIN:
        return redirect('admin_dashboard')
    elif request.user.role == User.RoleChoices.EMPLOYEE:
        return redirect('employee_dashboard')
    elif request.user.role == User.RoleChoices.CUSTOMER:
        return redirect('customer_dashboard')
    elif request.user.role == User.RoleChoices.RIDER:
        return redirect('delivery_dashboard')
    else:
        return redirect('login')

# --- ROLE DASHBOARDS (Placeholders) ---

from datetime import datetime

@login_required
def admin_dashboard(request):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    orders = Order.objects.all()
    
    total_orders = orders.count()
    total_income = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    paid_orders_count = orders.filter(payment_status=Order.PaymentStatusChoices.PAID).count()
    unpaid_orders_count = orders.filter(payment_status=Order.PaymentStatusChoices.UNPAID).count()
    
    completed_orders_count = orders.filter(status=Order.StatusChoices.COMPLETED).count()
    active_orders_count = orders.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).count()
    
    active_orders = orders.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).order_by('-created_at')[:5]
    pending_gcash = Order.objects.filter(payment_method=Order.PaymentMethodChoices.GCASH, payment_status=Order.PaymentStatusChoices.UNPAID).order_by('created_at')[:5]
    
    context = {
        'total_orders': total_orders,
        'total_income': total_income,
        'paid_orders_count': paid_orders_count,
        'unpaid_orders_count': unpaid_orders_count,
        'completed_orders_count': completed_orders_count,
        'active_orders_count': active_orders_count,
        'active_orders': active_orders,
        'pending_gcash': pending_gcash,
    }
    
    return render(request, 'core/admin/dashboard.html', context)

@login_required
def admin_analytics(request):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    filter_date_str = request.GET.get('date')
    filter_month_str = request.GET.get('month')
    quick_filter = request.GET.get('quick_filter')
    
    orders = Order.objects.all()
    selected_filter = "All Time"
    
    now = timezone.now()
    
    if filter_date_str:
        try:
            dt = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date=dt)
            selected_filter = f"Date: {dt.strftime('%B %d, %Y')}"
        except:
            pass
    elif filter_month_str:
        try:
            dt = datetime.strptime(filter_month_str, '%Y-%m').date()
            orders = orders.filter(created_at__year=dt.year, created_at__month=dt.month)
            selected_filter = f"Month: {dt.strftime('%B %Y')}"
        except:
            pass
    elif quick_filter:
        import datetime as dt_mod
        if quick_filter == 'today':
            orders = orders.filter(created_at__date=now.date())
            selected_filter = "Today"
        elif quick_filter == 'this_week':
            start_of_week = now.date() - dt_mod.timedelta(days=now.weekday())
            orders = orders.filter(created_at__date__gte=start_of_week)
            selected_filter = "This Week"
        elif quick_filter == 'this_month':
            orders = orders.filter(created_at__year=now.year, created_at__month=now.month)
            selected_filter = "This Month"
            
    # Top KPI Metrics
    total_orders = orders.count()
    completed_orders = orders.filter(status=Order.StatusChoices.COMPLETED).count()
    pending_orders = orders.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).count()
    
    paid_orders = orders.filter(payment_status=Order.PaymentStatusChoices.PAID)
    paid_orders_count = paid_orders.count()
    unpaid_orders_count = orders.filter(payment_status=Order.PaymentStatusChoices.UNPAID).count()
    
    total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0.0
    average_order_value = (total_revenue / paid_orders_count) if paid_orders_count > 0 else 0.0
    
    # Advanced Breakdown
    cash_orders = paid_orders.filter(payment_method=Order.PaymentMethodChoices.CASH)
    breakdown_cash = cash_orders.count()
    cash_total = cash_orders.aggregate(total=Sum('total_amount'))['total'] or 0.0
    
    gcash_orders = paid_orders.filter(payment_method=Order.PaymentMethodChoices.GCASH)
    breakdown_gcash = gcash_orders.count()
    gcash_total = gcash_orders.aggregate(total=Sum('total_amount'))['total'] or 0.0
    
    breakdown_paypal = paid_orders.filter(payment_method=Order.PaymentMethodChoices.PAYPAL).count()
    
    breakdown_walkin = orders.filter(order_type=Order.OrderTypeChoices.WALK_IN).count()
    breakdown_delivery = orders.filter(order_type=Order.OrderTypeChoices.DELIVERY).count()
    breakdown_appt = orders.filter(order_type=Order.OrderTypeChoices.APPOINTMENT).count()
    
    # Aggregations for Chart.js
    daily_stats = list(orders.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id'), revenue=Sum('total_amount')).order_by('day'))
    monthly_stats = list(orders.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id'), revenue=Sum('total_amount')).order_by('month'))
    
    orders_by_day = [{'x': d['day'].strftime('%Y-%m-%d'), 'y': d['count']} for d in daily_stats if d['day']]
    revenue_by_day = [{'x': d['day'].strftime('%Y-%m-%d'), 'y': float(d['revenue'] or 0)} for d in daily_stats if d['day']]
    
    orders_by_month = [{'x': d['month'].strftime('%Y-%m'), 'y': d['count']} for d in monthly_stats if d['month']]
    revenue_by_month = [{'x': d['month'].strftime('%Y-%m'), 'y': float(d['revenue'] or 0)} for d in monthly_stats if d['month']]
    
    # Also collect status breakdown
    status_counts = list(orders.values('status').annotate(count=Count('id')).order_by('-count'))
    status_labels = dict(Order.StatusChoices.choices)
    status_chart_data = [{'label': status_labels.get(item['status'], item['status']), 'count': item['count']} for item in status_counts]

    context = {
        'selected_filter': selected_filter,
        'filter_date_str': filter_date_str or '',
        'filter_month_str': filter_month_str or '',
        'quick_filter': quick_filter or '',
        
        # KPIs
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'paid_orders_count': paid_orders_count,
        'unpaid_orders_count': unpaid_orders_count,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        
        # Payment breakdown
        'breakdown_cash': breakdown_cash,
        'cash_total': cash_total,
        'breakdown_gcash': breakdown_gcash,
        'gcash_total': gcash_total,
        'breakdown_paypal': breakdown_paypal,
        
        # Order sources
        'breakdown_walkin': breakdown_walkin,
        'breakdown_delivery': breakdown_delivery,
        'breakdown_appt': breakdown_appt,
        
        # Chart data (JSON strings safely dumped for the template)
        'orders_by_day_json': json.dumps(orders_by_day),
        'revenue_by_day_json': json.dumps(revenue_by_day),
        'orders_by_month_json': json.dumps(orders_by_month),
        'revenue_by_month_json': json.dumps(revenue_by_month),
        'status_chart_json': json.dumps(status_chart_data),
    }
    return render(request, 'core/admin/analytics.html', context)

@login_required
def admin_queue(request):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    filter_date_str = request.GET.get('date')
    filter_month_str = request.GET.get('month')
    quick_filter = request.GET.get('quick_filter')
    
    # Machine Queue Operation States
    operational_statuses = [
        Order.StatusChoices.AT_SHOP,
        Order.StatusChoices.PROCESSING,
        Order.StatusChoices.READY_FOR_DELIVERY
    ]
    
    orders = Order.objects.filter(status__in=operational_statuses)
    
    selected_filter = "All Time"
    now = timezone.now()
    
    if filter_date_str:
        try:
            dt = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date=dt)
            selected_filter = f"Date: {dt.strftime('%B %d, %Y')}"
        except:
            pass
    elif filter_month_str:
        try:
            dt = datetime.strptime(filter_month_str, '%Y-%m').date()
            orders = orders.filter(created_at__year=dt.year, created_at__month=dt.month)
            selected_filter = f"Month: {dt.strftime('%B %Y')}"
        except:
            pass
    elif quick_filter:
        import datetime as dt_mod
        if quick_filter == 'today':
            orders = orders.filter(created_at__date=now.date())
            selected_filter = "Today"
        elif quick_filter == 'this_week':
            start_of_week = now.date() - dt_mod.timedelta(days=now.weekday())
            orders = orders.filter(created_at__date__gte=start_of_week)
            selected_filter = "This Week"
        elif quick_filter == 'this_month':
            orders = orders.filter(created_at__year=now.year, created_at__month=now.month)
            selected_filter = "This Month"
            
    # Explicitly pull in relationships to dodge N+1 queries natively in the template iteration
    active_orders = orders.select_related(
        'customer', 'employee', 'rider'
    ).prefetch_related(
        'items', 'items__service', 'items__product'
    ).order_by('created_at')
    
    active_orders_list = list(active_orders)
    
    # Calculate live queue statistics based on the extracted scope 
    total_orders_in_queue = len(active_orders_list)
    at_shop_count = len([o for o in active_orders_list if o.status == Order.StatusChoices.AT_SHOP])
    processing_count = len([o for o in active_orders_list if o.status == Order.StatusChoices.PROCESSING])
    ready_count = len([o for o in active_orders_list if o.status == Order.StatusChoices.READY_FOR_DELIVERY])
    
    context = {
        'selected_filter': selected_filter,
        'filter_date_str': filter_date_str or '',
        'filter_month_str': filter_month_str or '',
        'quick_filter': quick_filter or '',
        
        'active_orders': active_orders_list,
        'active_orders_count': total_orders_in_queue,
        'at_shop_count': at_shop_count,
        'processing_count': processing_count,
        'ready_count': ready_count,
    }
    return render(request, 'core/admin/queue.html', context)

@login_required
def admin_payments(request):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    pending_gcash = Order.objects.filter(payment_method=Order.PaymentMethodChoices.GCASH, payment_status=Order.PaymentStatusChoices.UNPAID).order_by('created_at')
    
    context = {
        'pending_gcash': pending_gcash,
    }
    return render(request, 'core/admin/payments.html', context)

@login_required
def admin_users(request):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    customers_count = User.objects.filter(role=User.RoleChoices.CUSTOMER).count()
    employees_count = User.objects.filter(role=User.RoleChoices.EMPLOYEE).count()
    recent_users = User.objects.exclude(id=request.user.id).order_by('-date_joined')[:20]
    
    context = {
        'customers_count': customers_count,
        'employees_count': employees_count,
        'recent_users': recent_users
    }
    return render(request, 'core/admin/users.html', context)

@login_required
def add_user(request):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request_user=request.user)
        if form.is_valid():
            new_user = form.save()
            messages.success(request, f'Account for {new_user.username} created successfully!')
            return redirect('admin_users')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm(request_user=request.user)
        
    return render(request, 'core/admin/add_user.html', {'form': form})

@login_required
def employee_dashboard(request):
    if request.user.role != User.RoleChoices.EMPLOYEE:
         return redirect('dashboard')
         
    profile = getattr(request.user, 'employee_profile', None)
    
    # Personal Stats
    today = timezone.now().date()
    orders_processed_today = Order.objects.filter(
        employee=request.user, 
        created_at__date=today
    ).count()
    
    total_processed = profile.orders_processed if profile else 0
    
    # Active Shared Processing Queue
    shared_active_orders = Order.objects.prefetch_related('items__service', 'items__product').filter(
        order_type__in=[Order.OrderTypeChoices.DELIVERY, Order.OrderTypeChoices.APPOINTMENT, Order.OrderTypeChoices.DROP_OFF]
    ).exclude(
        status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]
    ).order_by('created_at')
    
    # My Active Walk-in Orders (Used for metrics, excludes COMPLETED/CANCELLED)
    my_walkin_orders = Order.objects.prefetch_related('items__service', 'items__product').filter(
        order_type=Order.OrderTypeChoices.WALK_IN,
        employee=request.user
    ).exclude(
        status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]
    ).order_by('created_at')
    
    # My Completed Walk-in Orders
    my_completed_walkin_orders = Order.objects.prefetch_related('items__service', 'items__product').filter(
        order_type=Order.OrderTypeChoices.WALK_IN,
        employee=request.user,
        status=Order.StatusChoices.COMPLETED
    ).order_by('-updated_at')[:20]
    
    # Bundle Walk-In Groups dynamically for Dashboard Rendering
    walkin_groups = [
        {'title': 'At Shop', 'icon': 'home', 'orders': []},
        {'title': 'Processing', 'icon': 'loader', 'orders': []},
        {'title': 'Ready for Pickup / Delivery', 'icon': 'package', 'orders': []},
        {'title': 'Completed', 'icon': 'check-circle', 'orders': []}
    ]
    
    for order in my_walkin_orders:
        if order.status in [Order.StatusChoices.AT_SHOP, Order.StatusChoices.PENDING_ACCEPTANCE, Order.StatusChoices.EXPECTING_DROP_OFF, Order.StatusChoices.RIDER_ACCEPTED, Order.StatusChoices.PICKED_UP]:
            walkin_groups[0]['orders'].append(order)
        elif order.status == Order.StatusChoices.PROCESSING:
            walkin_groups[1]['orders'].append(order)
        elif order.status in [Order.StatusChoices.READY_FOR_DELIVERY, Order.StatusChoices.OUT_FOR_DELIVERY]:
            walkin_groups[2]['orders'].append(order)
            
    for order in my_completed_walkin_orders:
        walkin_groups[3]['orders'].append(order)
    
    # Shared Completed Orders (Excludes WALK_IN)
    completed_orders = Order.objects.prefetch_related('items__service', 'items__product').filter(
        order_type__in=[Order.OrderTypeChoices.DELIVERY, Order.OrderTypeChoices.APPOINTMENT, Order.OrderTypeChoices.DROP_OFF]
    ).filter(
        status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]
    ).order_by('-updated_at')[:30]
    
    pickup_appointments = Appointment.objects.filter(
        status=Appointment.StatusChoices.PENDING,
        appointment_type=Appointment.TypeChoices.PICKUP
    ).order_by('appointment_date')
    
    # We still calculate total active queue length for the metric
    total_active_queue = shared_active_orders.count() + my_walkin_orders.count()
    
    context = {
        'orders_processed_today': orders_processed_today,
        'total_processed': total_processed,
        'shared_active_orders': shared_active_orders,
        'my_walkin_orders': my_walkin_orders,
        'walkin_groups': walkin_groups,
        'completed_orders': completed_orders,
        'pickup_appointments': pickup_appointments,
        'active_queue_count': total_active_queue,
        'today': today
    }
    
    return render(request, 'core/employee/dashboard.html', context)

@login_required
def verify_gcash_payment(request, order_id):
    if request.user.role != User.RoleChoices.ADMIN:
        return redirect('dashboard')
        
    order = get_object_or_404(Order, id=order_id)
    if order.payment_method == 'GCASH' and order.payment_status == 'UNPAID':
        order.payment_status = 'PAID'
        order.save()
        messages.success(request, f'GCash payment for Order #{order.id} verified successfully.')
    else:
        messages.error(request, 'This order is not eligible for GCash verification.')
        
    return redirect('admin_dashboard')

# --- EMPLOYEE ACTIONS ---
@login_required
def update_order_status(request, order_id):
    if request.user.role not in [User.RoleChoices.EMPLOYEE, User.RoleChoices.ADMIN, User.RoleChoices.RIDER]:
        return redirect('dashboard')
        
    order = get_object_or_404(Order, id=order_id)
    
    # ENFORCE EMPLOYEE OWNERSHIP
    if request.user.role == User.RoleChoices.EMPLOYEE:
        # Only block if it is a walk-in order created by ANOTHER employee
        if order.order_type == Order.OrderTypeChoices.WALK_IN:
            if order.employee and order.employee != request.user:
                messages.error(request, 'You do not have permission to edit this walk-in order.')
                return redirect('employee_dashboard')
            
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.StatusChoices.choices):
            
            # --- BACKEND VALIDATION ---
            if request.user.role == User.RoleChoices.EMPLOYEE:
                invalid_employee_statuses = [
                    Order.StatusChoices.PENDING_ACCEPTANCE,
                    Order.StatusChoices.RIDER_ACCEPTED,
                    Order.StatusChoices.PICKED_UP,
                    Order.StatusChoices.OUT_FOR_DELIVERY
                ]
                if new_status in invalid_employee_statuses:
                    messages.error(request, 'Employees cannot set rider-specific statuses.')
                    return redirect('employee_dashboard')

            if request.user.role == User.RoleChoices.RIDER:
                invalid_rider_statuses = [
                    Order.StatusChoices.AT_SHOP,
                    Order.StatusChoices.PROCESSING,
                    Order.StatusChoices.READY_FOR_DELIVERY
                ]
                if new_status in invalid_rider_statuses:
                    messages.error(request, 'Riders cannot set shop processing statuses.')
                    return redirect('delivery_dashboard')
                    
            order.status = new_status
            
            # Claim unassigned shared orders when an employee progresses them
            if request.user.role == User.RoleChoices.EMPLOYEE and not order.employee:
                order.employee = request.user
                
            # If rider accepts, picks up, or starts a delivery, claim it
            if request.user.role == User.RoleChoices.RIDER and new_status in [Order.StatusChoices.RIDER_ACCEPTED, Order.StatusChoices.PICKED_UP, Order.StatusChoices.OUT_FOR_DELIVERY]:
                if not order.rider:
                    order.rider = request.user
                    
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}.')
            
    if request.user.role == User.RoleChoices.RIDER:
        return redirect('delivery_dashboard')
    elif request.user.role == User.RoleChoices.ADMIN:
        return redirect('admin_dashboard')
    
    return redirect('employee_dashboard')

from django.http import JsonResponse # type: ignore
from django.db.models import Q # type: ignore

@login_required
def employee_pos_customer_api(request):
    if request.user.role not in [User.RoleChoices.EMPLOYEE, User.RoleChoices.ADMIN]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
        
    # Search for customer users by username, first name, last name
    customers = User.objects.filter(
        role=User.RoleChoices.CUSTOMER
    ).filter(
        Q(username__icontains=query) | 
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query)
    ).values('id', 'username', 'first_name', 'last_name')[:10]
    
    results = [
        {
            'id': c['id'],
            'username': c['username'],
            'full_name': f"{c['first_name']} {c['last_name']}".strip() or c['username']
        }
        for c in customers
    ]
    return JsonResponse({'results': results})

@login_required
def employee_pos(request):
    if request.user.role not in [User.RoleChoices.EMPLOYEE, User.RoleChoices.RIDER]:
        return redirect('dashboard')
        
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        walkin_name_raw = request.POST.get('walkin_name')
        walkin_name = walkin_name_raw.strip() if walkin_name_raw else None
        payment_method = request.POST.get('payment_method')
        payment_reference = request.POST.get('payment_reference')
        order_data_str = request.POST.get('order_data')
        
        if payment_method == 'GCASH' and not payment_reference:
            messages.error(request, 'GCash payments require a reference number.')
            return redirect('employee_pos')
            
        try:
            cart = json.loads(order_data_str)
        except:
            messages.error(request, 'Invalid cart data.')
            return redirect('employee_pos')
            
        if not cart:
            messages.error(request, 'Cart is empty.')
            return redirect('employee_pos')
            
        customer = None
        walkin_name_val = None
        if customer_id:
            customer = User.objects.filter(username=customer_id, role=User.RoleChoices.CUSTOMER).first()
            if not customer and customer_id.isdigit():
                customer = User.objects.filter(id=customer_id, role=User.RoleChoices.CUSTOMER).first()
                
        if walkin_name and not customer:
            walkin_name_val = walkin_name
                
        total = sum(item['total'] for item in cart)
        
        # If Rider, map them. If Employee, map them.
        is_rider = request.user.role == User.RoleChoices.RIDER
        
        # If there's an appointment associated (passed via GET args to the template and submitted back), mark it complete
        appointment_id = request.GET.get('appointment_id') or request.POST.get('appointment_id')
        
        assigned_order_type = Order.OrderTypeChoices.APPOINTMENT if appointment_id else Order.OrderTypeChoices.WALK_IN
        
        order = Order.objects.create(
            customer=customer,
            walkin_name=walkin_name_val,
            employee=request.user if not is_rider else None,
            rider=request.user if is_rider else None,
            status=Order.StatusChoices.PICKED_UP if is_rider else Order.StatusChoices.PROCESSING,
            payment_method=payment_method,
            payment_status=Order.PaymentStatusChoices.PAID if payment_method == 'CASH' else Order.PaymentStatusChoices.UNPAID,
            payment_reference=payment_reference if payment_method == 'GCASH' else None,
            total_amount=total,
            order_type=assigned_order_type
        )
        
        if appointment_id:
            try:
                appt = Appointment.objects.get(id=appointment_id)
                appt.status = Appointment.StatusChoices.COMPLETED
                appt.save()
            except Appointment.DoesNotExist:
                pass
        
        for item in cart:
            item_type = item.get('item_type', 'SERVICE' if item['type'] == 'Service' else 'PRODUCT')
            load_index = item.get('load_index', None)
            notes_text = item.get('notes', '')
            
            if item['type'] == 'Service':
                service = Service.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order, 
                    service=service, 
                    quantity=item['qty'], 
                    price=item['price'],
                    item_type=item_type,
                    load_index=load_index,
                    notes=notes_text
                )
            else:
                product = Product.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order, 
                    product=product, 
                    quantity=item['qty'], 
                    price=item['price'],
                    item_type=item_type,
                    load_index=load_index
                )
                
        # Generate QR code
        qr_url = request.build_absolute_uri(f'/receipt/{order.receipt_token}/')
        qr = qrcode.make(qr_url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        order.qr_code.save(f'order_{order.id}_qr.png', ContentFile(buffer.getvalue()), save=False)
        order.save()
            
        # Increment Employee Stats if applicable
        profile = getattr(request.user, 'employee_profile', None)
        if profile and not is_rider:
            profile.orders_processed += 1
            profile.save()
            
        if payment_method == 'GCASH':
            messages.warning(request, f'Order #{order.id} submitted. GCash payment is pending Admin verification.')
        else:
            messages.success(request, f'Order #{order.id} created successfully.')
        
        if is_rider:
            return redirect('delivery_dashboard')
        return redirect('employee_dashboard')
        
    services = Service.objects.filter(is_active=True)
    products = Product.objects.all()
    
    # Pre-fill customer ID from GET request if provided (e.g., from process_appointment redirect)
    initial_customer_id = request.GET.get('customer_id', '')
    appointment_id = request.GET.get('appointment_id', '')
    
    context = {
        'services': services,
        'products': products,
        'initial_customer_id': initial_customer_id,
        'appointment_id': appointment_id
    }
    
    return render(request, 'core/employee/pos.html', context)

@login_required
def customer_dashboard(request):
    if request.user.role != User.RoleChoices.CUSTOMER:
         return redirect('dashboard')
         
    active_orders = request.user.customer_orders.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).order_by('-created_at')
    appointments = request.user.appointments.filter(status__in=[Appointment.StatusChoices.PENDING, Appointment.StatusChoices.CONFIRMED]).order_by('appointment_date')
    
    context = {
        'active_orders': active_orders,
        'appointments': appointments,
    }
    return render(request, 'core/customer/dashboard.html', context)

@login_required
def customer_history(request):
    if request.user.role != User.RoleChoices.CUSTOMER:
         return redirect('dashboard')
    
    past_orders = request.user.customer_orders.filter(
        status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]
    ).order_by('-created_at')
    
    return render(request, 'core/customer/history.html', {'past_orders': past_orders})

@login_required
def customer_create_order(request):
    if request.user.role != User.RoleChoices.CUSTOMER:
        return redirect('dashboard')
        
    # Seed predefined services and products
    services_seed = [
        {"name": "Wash & Dry", "price": 100.00},
        {"name": "Wash Only", "price": 60.00},
        {"name": "Dry Only", "price": 50.00},
    ]
    products_seed = [
        {"name": "Fabricon", "price": 15.00},
        {"name": "Detergent", "price": 15.00},
    ]
    
    for s in services_seed:
        Service.objects.get_or_create(name=s["name"], defaults={"price": s["price"]})
    for p in products_seed:
        Product.objects.get_or_create(name=p["name"], defaults={"price": p["price"]})
        
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            loads_data = payload.get('loads', [])
            delivery_method = payload.get('delivery_method', 'DROP_OFF')
            
            if not loads_data:
                return JsonResponse({'success': False, 'message': 'No loads provided.'}, status=400)
                
            total_amount: float = 0.0
            order_items_to_create = []
            
            global_load_index = 0
            
            for load in loads_data:
                # Get selected service metadata
                service_id = load.get('service_id')
                weight = float(load.get('weight', 0))
                
                if weight > 7:
                    return JsonResponse({'success': False, 'message': 'Each load can only handle up to 7kg. Please add another load.'}, status=400)
                    
                service = get_object_or_404(Service, id=service_id)
                
                has_fabricon = load.get('fabricon')
                has_detergent = load.get('detergent')
                
                fabricon_qty = int(load.get('fabricon_qty', 1)) if has_fabricon else 0
                detergent_qty = int(load.get('detergent_qty', 1)) if has_detergent else 0
                
                fabricon_obj = Product.objects.filter(name__icontains="Fabric").first() if fabricon_qty > 0 else None
                detergent_obj = Product.objects.filter(name__icontains="Detergent").first() if detergent_qty > 0 else None
                
                load_notes = load.get('notes', '')
                
                global_load_index = global_load_index + 1 # type: ignore
                current_load_id = global_load_index
                
                # 1. Add Service Load
                s_price = getattr(service, 'price', 0.0)
                total_amount = float(total_amount) + float(s_price) # type: ignore
                order_items_to_create.append({
                    'type': 'Service',
                    'item_type': 'SERVICE',
                    'load_index': current_load_id,
                    'obj': service,
                    'qty': 1,
                    'price': getattr(service, 'price', 0.0),
                    'notes': load_notes
                })
                
                # 2. Add Add-ons for this specific load
                if fabricon_obj is not None and fabricon_qty > 0:
                    fab_price = getattr(fabricon_obj, 'price', 0.0) * fabricon_qty # type: ignore
                    total_amount = float(total_amount) + float(fab_price) # type: ignore
                    order_items_to_create.append({
                        'type': 'Product',
                        'item_type': 'ADDON',
                        'load_index': current_load_id,
                        'obj': fabricon_obj,
                        'qty': fabricon_qty,
                        'price': getattr(fabricon_obj, 'price', 0.0)
                    })
                    
                if detergent_obj is not None and detergent_qty > 0:
                    det_price = getattr(detergent_obj, 'price', 0.0) * detergent_qty # type: ignore
                    total_amount = float(total_amount) + float(det_price) # type: ignore
                    order_items_to_create.append({
                        'type': 'Product',
                        'item_type': 'ADDON',
                        'load_index': current_load_id,
                        'obj': detergent_obj,
                        'qty': detergent_qty,
                        'price': getattr(detergent_obj, 'price', 0.0)
                    })

            # Create Order
            scheduled_pickup_dt = None
            if delivery_method == 'PICKUP':
                pickup_time_str = payload.get('pickup_datetime')
                if pickup_time_str:
                    from django.utils.dateparse import parse_datetime # type: ignore
                    scheduled_pickup_dt = parse_datetime(pickup_time_str)
                    
            new_order = Order.objects.create(
                customer=request.user,
                status=Order.StatusChoices.EXPECTING_DROP_OFF if delivery_method == 'DROP_OFF' else Order.StatusChoices.PENDING_ACCEPTANCE,
                payment_method=Order.PaymentMethodChoices.CASH,
                payment_status=Order.PaymentStatusChoices.UNPAID,
                total_amount=total_amount,
                scheduled_pickup=scheduled_pickup_dt,
                order_type=Order.OrderTypeChoices.DROP_OFF if delivery_method == 'DROP_OFF' else Order.OrderTypeChoices.DELIVERY
            )
            
            # Create Order Items
            for item in order_items_to_create:
                if item['type'] == 'Service':
                    OrderItem.objects.create(
                        order=new_order, 
                        service=item['obj'], 
                        quantity=item['qty'], 
                        price=item['price'],
                        item_type=item.get('item_type', 'SERVICE'),
                        load_index=item.get('load_index'),
                        notes=item.get('notes', '')
                    )
                else:
                    OrderItem.objects.create(
                        order=new_order, 
                        product=item['obj'], 
                        quantity=item['qty'], 
                        price=item['price'],
                        item_type=item.get('item_type', 'PRODUCT'),
                        load_index=item.get('load_index')
                    )
                    
            # Generate QR code
            qr_url = request.build_absolute_uri(f'/receipt/{new_order.receipt_token}/')
            qr_img = qrcode.make(qr_url)
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            new_order.qr_code.save(f'order_{new_order.id}_qr.png', ContentFile(buffer.getvalue()), save=False)
            new_order.save()
                
            messages.success(request, f'Order #{new_order.id} has been submitted successfully!')
            return JsonResponse({'success': True, 'redirect_url': '/customer-dashboard/'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    services = Service.objects.all()
    products = Product.objects.all()
    context = {
        'services': services,
        'products': products
    }
    return render(request, 'core/customer/order_form.html', context)


@login_required
def delivery_dashboard(request):
    if request.user.role != User.RoleChoices.RIDER:
         return redirect('dashboard')
         
    # Available Jobs (Pending Acceptance)
    available_jobs = Order.objects.filter(
        status=Order.StatusChoices.PENDING_ACCEPTANCE,
        scheduled_pickup__isnull=False
    ).order_by('scheduled_pickup')
    
    # My Accepted Jobs (Driving to customer)
    accepted_jobs = Order.objects.filter(
        status=Order.StatusChoices.RIDER_ACCEPTED,
        rider=request.user
    ).order_by('-updated_at')
    
    # My Pickups (Picked Up - Driving back to shop)
    my_pickups = Order.objects.filter(
        status=Order.StatusChoices.PICKED_UP,
        rider=request.user
    ).order_by('-updated_at')
    # My accepted deliveries (Out for delivery or claimed Ready for Delivery)
    deliveries = Order.objects.filter(
        status__in=[Order.StatusChoices.READY_FOR_DELIVERY, Order.StatusChoices.OUT_FOR_DELIVERY],
        rider=request.user
    ).order_by('-updated_at')
    
    # Available Deliveries (Ready for Delivery but no rider claimed it yet, and must be DELIVERY type)
    available_deliveries = Order.objects.filter(
        status=Order.StatusChoices.READY_FOR_DELIVERY,
        order_type=Order.OrderTypeChoices.DELIVERY,
        rider__isnull=True
    ).order_by('updated_at')
    
    context = {
        'available_jobs': available_jobs,
        'accepted_jobs': accepted_jobs,
        'my_pickups': my_pickups,
        'deliveries': deliveries,
        'available_deliveries': available_deliveries
    }
    
    return render(request, 'core/delivery/dashboard.html', context)

@login_required
def delivery_history(request):
    if request.user.role != User.RoleChoices.RIDER:
        return redirect('dashboard')
        
    past_jobs = Order.objects.prefetch_related('items__service', 'items__product').filter(
        rider=request.user,
        status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]
    ).order_by('-updated_at')
    
    context = {
        'past_jobs': past_jobs
    }
    
    return render(request, 'core/delivery/history.html', context)

# --- RECEIPT ---
@login_required
def order_receipt(request, receipt_token):
    order = get_object_or_404(Order, receipt_token=receipt_token)
    # Both customer and employee can view it
    if request.user.role == User.RoleChoices.CUSTOMER and order.customer != request.user:
        return redirect('dashboard')
    
    return render(request, 'core/receipt.html', {'order': order})

# --- APPOINTMENT LOGIC ---
@login_required
def book_appointment(request):
    if request.method == 'POST':
        apt_type = request.POST.get('appointment_type')
        apt_date = request.POST.get('appointment_date')
        
        # Validation could be added here (e.g. checking for past dates)
        
        Appointment.objects.create(
            customer=request.user,
            appointment_type=apt_type,
            appointment_date=apt_date
        )
        
        messages.success(request, 'Appointment booked successfully!')
        return redirect('customer_dashboard')
        
    return redirect('dashboard')

@login_required
def process_appointment(request, appointment_id):
    """
    Called by a Rider or Employee to "pick up" a pending pickup appointment.
    We just redirect them to the POS to fill in the exact loads.
    """
    if request.user.role not in [User.RoleChoices.EMPLOYEE, User.RoleChoices.RIDER]:
        return redirect('dashboard')
        
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        if appointment.status != Appointment.StatusChoices.PENDING:
            messages.error(request, 'This appointment is no longer pending.')
            return redirect('delivery_dashboard')
        elif appointment.appointment_type != Appointment.TypeChoices.PICKUP:
            messages.error(request, 'Only pickup appointments can be converted to orders this way.')
            return redirect('delivery_dashboard')
        else:
            # Redirect to POS with prefilled customer data and the appointment ID
            from urllib.parse import urlencode
            base_url = reverse('employee_pos')
            query_string = urlencode({
                'customer_id': appointment.customer.username, 
                'appointment_id': appointment.id
            })
            return redirect(f"{base_url}?{query_string}")
