import os
import django # type: ignore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laundry_pos.settings")
django.setup()

from core.models import Service, Product # type: ignore

# Clear existing if needed, or just update/create
# I'll use update_or_create to avoid duplicates

# Services
services_data = [
    {"name": "Wash & Dry", "price": 100.00, "description": "Up to 7kg per load"},
    {"name": "Wash Only", "price": 60.00, "description": "Up to 7kg per load"},
    {"name": "Dry Only", "price": 50.00, "description": "Up to 7kg per load"},
]

for s_data in services_data:
    Service.objects.update_or_create(
        name=s_data["name"],
        defaults={"price": s_data["price"], "description": s_data["description"], "is_active": True}
    )
    print(f"Service '{s_data['name']}' created/updated.")

# Products
products_data = [
    {"name": "Detergent", "price": 15.00, "description": "1 sachet/bottle"},
    {"name": "Fabric Conditioner", "price": 15.00, "description": "1 sachet/bottle"},
]

for p_data in products_data:
    Product.objects.update_or_create(
        name=p_data["name"],
        defaults={"price": p_data["price"], "description": p_data["description"], "stock": 100} # default stock 100
    )
    print(f"Product '{p_data['name']}' created/updated.")
