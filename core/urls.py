from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_customer_view, name='register'),
    
    # Landing Page
    path('', views.home, name='home'),
    
    # Dashboard Redirector
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-queue/', views.admin_queue, name='admin_queue'),
    path('admin-payments/', views.admin_payments, name='admin_payments'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-add-user/', views.add_user, name='add_user'),
    path('admin-verify-gcash/<int:order_id>/', views.verify_gcash_payment, name='verify_gcash'),
    
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('delivery-dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery-history/', views.delivery_history, name='delivery_history'),
    
    # Customer Actions
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('customer-history/', views.customer_history, name='customer_history'),
    path('customer-create-order/', views.customer_create_order, name='customer_create_order'),
    path('profile/', views.customer_profile, name='customer_profile'),
    
    # Employee Actions
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('mark-paid/<int:order_id>/', views.mark_order_paid, name='mark_order_paid'),
    path('process-appointment/<int:appointment_id>/', views.process_appointment, name='process_appointment'),
    path('pos/api/customers/', views.employee_pos_customer_api, name='employee_pos_customer_api'),
    path('pos/', views.employee_pos, name='employee_pos'),
    
    # Shared
    path('receipt/<str:receipt_token>/', views.order_receipt, name='order_receipt'),

    # AI Chatbot
    path('chatbot/', views.chatbot_api, name='chatbot_api'),
]
