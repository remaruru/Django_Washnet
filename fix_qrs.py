import os
import django
from io import BytesIO

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laundry_pos.settings')
django.setup()

from core.models import Order
from django.core.files.base import ContentFile
import qrcode

# Render natively sets 'RENDER_EXTERNAL_HOSTNAME' in the environment.
# If not present, default to localhost.
DOMAIN = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '127.0.0.1:8000')
PROTOCOL = 'https' if 'onrender.com' in DOMAIN else 'http'

def generate_missing_qrs():
    # Find all orders and aggressively regenerate to fix broken local links
    orders = Order.objects.all()
    
    count = orders.count()
    if count == 0:
        print("No orders exist in the database! Nothing to do.")
        return

    print(f"Aggressively regenerating QR codes for {count} orders to force Cloudinary sync...")
    
    success_count = 0
    for order in orders:
        try:
            # Build the absolute URL
            qr_url = f"{PROTOCOL}://{DOMAIN}/receipt/{order.receipt_token}/"
            
            # Generate the QR image
            qr_img = qrcode.make(qr_url)
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            
            # Save the file. CloudinaryStorage will intercept this and upload it.
            order.qr_code.save(f'order_{order.id}_qr.png', ContentFile(buffer.getvalue()), save=True)
            
            print(f"  + Generated and uploaded QR for Order #{order.id}")
            success_count += 1
        except Exception as e:
            print(f"  - Failed to generate QR for Order #{order.id}: {e}")

    print(f"Finished. Successfully generated {success_count} missing QR codes.")

if __name__ == "__main__":
    generate_missing_qrs()
