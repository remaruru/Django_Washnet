import os
import django # type: ignore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laundry_pos.settings")
django.setup()

from django.contrib.auth import get_user_model # type: ignore
User = get_user_model()

# SUPER User (DjangoSide)
try:
    if not User.objects.filter(username='gelo').exists():
        su = User.objects.create_superuser('gelo', '', 'gelo')
        su.role = 'ADMIN'
        su.save()
        print("Superuser 'gelo' created.")
    else:
        print("Superuser 'gelo' already exists.")
except Exception as e:
    print(f"Error creating superuser 'gelo': {e}")

# ADMIN
try:
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@laundry.com', 'admin')
        admin.role = 'ADMIN'
        admin.save()
        print("Admin user 'admin' created.")
    else:
        print("Admin user 'admin' already exists.")
except Exception as e:
    print(f"Error creating admin 'admin': {e}")

# customer
try:
    if not User.objects.filter(username='customer').exists():
        cust = User.objects.create_user('customer', 'customer@laundry.com', 'customer')
        cust.role = 'CUSTOMER'
        cust.save()
        print("Customer user 'customer' created.")
    else:
        print("Customer user 'customer' already exists.")
except Exception as e:
    print(f"Error creating customer: {e}")

# employee
try:
    if not User.objects.filter(username='employee').exists():
        emp = User.objects.create_user('employee', 'employee@laundry.com', 'gelo1234')
        emp.role = 'EMPLOYEE'
        emp.is_staff = True # Usually employees need staff access
        emp.save()
        print("Employee user 'employee' created.")
    else:
        print("Employee user 'employee' already exists.")
except Exception as e:
    print(f"Error creating employee: {e}")

# rider
try:
    if not User.objects.filter(username='rider').exists():
        rid = User.objects.create_user('rider', 'rider@laundry.com', 'gelo1234')
        rid.role = 'RIDER'
        rid.is_staff = True # Riders may need somewhat restricted staff access depending on your system, but leaving this optional
        rid.save()
        print("Rider user 'rider' created.")
    else:
        print("Rider user 'rider' already exists.")
except Exception as e:
    print(f"Error creating rider: {e}")
