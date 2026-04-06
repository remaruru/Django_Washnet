"""
chatbot_tools.py
────────────────
All database query functions available to the Washnet AI chatbot.
Each function is called by the chatbot_api view after Gemini requests it via
function calling. Functions are grouped by the minimum role required to access them.

Role hierarchy (additive):
  ANONYMOUS  → faq, estimate_price
  CUSTOMER   → + track_order (receipt token only)
  EMPLOYEE   → + get_today_queue, get_processing_counts, get_walkin_summary,
                  lookup_order (token OR order ID), get_unpaid_orders,
                  get_ready_for_delivery, get_operational_counts
  ADMIN      → + get_orders_summary, get_revenue_summary,
                  get_payment_breakdown, get_analytics_summary
"""

from django.utils import timezone
from django.db.models import Sum, Count, Q
from core.models import Order, Service               # type: ignore

import datetime

# ─────────────────────────────────────────────────────────────────
#  FAQ CONFIG — fill in real values before going live
# ─────────────────────────────────────────────────────────────────
FAQ_DATA = {
    "hours": {
        "title": "Store Hours",
        # TODO: Replace with actual store hours
        "answer": "[STORE_HOURS_PLACEHOLDER] — Please contact Washnet directly for current store hours.",
    },
    "delivery": {
        "title": "Delivery Availability",
        # TODO: Replace with actual delivery coverage details
        "answer": "[DELIVERY_AREA_PLACEHOLDER] — Delivery availability and coverage area to be confirmed by the store.",
    },
    "pickup_dropoff": {
        "title": "Pickup & Drop-Off Flow",
        "answer": (
            "For drop-off: bring your laundry to the shop during business hours. "
            "An employee will weigh and process your items. "
            "For pickup orders: book an appointment through the app and a rider will collect your laundry from your address."
        ),
    },
    "payment": {
        "title": "Payment Methods",
        "answer": "We accept Cash, GCash, and PayPal. GCash payments require a valid reference number for verification.",
    },
    "how_to_order": {
        "title": "How to Place an Order",
        "answer": (
            "You can place an order in three ways: "
            "(1) Walk in to the shop directly, "
            "(2) Book a pickup appointment via the app — a rider will collect your laundry, "
            "(3) Drop off your laundry yourself and an employee will process it. "
            "After your laundry is processed, you will receive a receipt token to track your order."
        ),
    },
    "services": {
        "title": "Available Services",
        "answer": "Use the price estimator to see all current services and their rates. Main services include washing, drying, and combined wash-and-dry options.",
    },
}

FAQ_ALIAS = {
    # Map common natural language topics to FAQ_DATA keys
    "store hours": "hours",
    "open": "hours",
    "opening": "hours",
    "closing": "hours",
    "schedule": "hours",
    "delivery": "delivery",
    "deliver": "delivery",
    "coverage": "delivery",
    "area": "delivery",
    "pickup": "pickup_dropoff",
    "drop off": "pickup_dropoff",
    "dropoff": "pickup_dropoff",
    "drop-off": "pickup_dropoff",
    "payment": "payment",
    "pay": "payment",
    "gcash": "payment",
    "cash": "payment",
    "how to order": "how_to_order",
    "place order": "how_to_order",
    "book": "how_to_order",
    "services": "services",
    "what services": "services",
}


# ─────────────────────────────────────────────────────────────────
#  ANONYMOUS / PUBLIC TOOLS
# ─────────────────────────────────────────────────────────────────

def faq(topic: str) -> dict:
    """Return a FAQ answer for the given topic keyword."""
    key = FAQ_ALIAS.get(topic.lower().strip())
    if key and key in FAQ_DATA:
        data = FAQ_DATA[key]
        return {"found": True, "title": data["title"], "answer": data["answer"]}
    # Attempt partial keyword match
    for alias, k in FAQ_ALIAS.items():
        if alias in topic.lower():
            data = FAQ_DATA[k]
            return {"found": True, "title": data["title"], "answer": data["answer"]}
    # Return all topic categories if no match
    topics_list = list(set(FAQ_DATA.keys()))
    return {
        "found": False,
        "message": "I couldn't find a specific answer for that. Here are the topics I can help with.",
        "available_topics": topics_list,
    }


def estimate_price(service_name: str, quantity_kg: float) -> dict:
    """
    Estimate total price for a given service and weight.
    Fetches live price from the Service table.
    """
    try:
        qty = float(quantity_kg)
    except (ValueError, TypeError):
        return {"error": "Invalid quantity. Please provide a number (e.g. 3.5 for 3.5kg)."}

    # Case-insensitive partial match
    service = Service.objects.filter(name__icontains=service_name, is_active=True).first()
    if not service:
        active_services = list(Service.objects.filter(is_active=True).values("name", "price"))
        # Clean up Decimal values for JSON serialization
        for svc in active_services:
            svc["price"] = float(svc["price"])
            
        return {
            "error": f"No active service found matching '{service_name}'.",
            "available_services": active_services,
        }

    unit_price = float(service.price)
    total = unit_price * qty
    return {
        "service": service.name,
        "unit_price": unit_price,
        "quantity_kg": qty,
        "estimated_total": round(total, 2),
        "note": "Final price may vary depending on actual weight at the shop.",
    }


def get_all_services() -> dict:
    """Return all active services and their prices."""
    services = list(Service.objects.filter(is_active=True).values("name", "price", "description"))
    for svc in services:
        svc["price"] = float(svc["price"])
        
    return {"services": services, "count": len(services)}


# ─────────────────────────────────────────────────────────────────
#  CUSTOMER TOOLS  (receipt token only — no name lookup)
# ─────────────────────────────────────────────────────────────────

def track_order(receipt_token: str, customer_user=None) -> dict:
    """
    Look up an order by receipt token.
    If customer_user is provided, enforce ownership check.
    """
    token = receipt_token.strip() if receipt_token else ""
    if not token:
        return {"error": "Please provide your receipt token to track your order."}

    try:
        order = Order.objects.select_related("customer", "rider", "employee").get(receipt_token=token)
    except Order.DoesNotExist:
        return {"error": f"No order found with receipt token '{token}'. Please check your token and try again."}

    # Ownership check for customers
    if customer_user is not None:
        if order.customer and order.customer != customer_user:
            return {"error": "This receipt token does not match your account. Please check your token."}
        if order.customer is None:
            # Walk-in order — cannot verify ownership, show limited info only
            return {
                "order_id": order.id,
                "status": order.get_status_display(),
                "payment_status": order.get_payment_status_display(),
                "note": "This is a walk-in order and cannot be claimed by an account.",
            }

    rider_name = order.rider.get_full_name() or order.rider.username if order.rider else None
    return {
        "order_id": order.id,
        "receipt_token": order.receipt_token,
        "status": order.get_status_display(),
        "order_type": order.get_order_type_display(),
        "payment_status": order.get_payment_status_display(),
        "payment_method": order.get_payment_method_display(),
        "total_amount": float(order.total_amount),
        "rider": rider_name,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "updated_at": order.updated_at.strftime("%Y-%m-%d %H:%M"),
    }


def get_my_orders(customer_user=None) -> dict:
    """
    Return all recent orders belonging to the customer.
    This eliminates the need for them to memorize and input receipt tokens.
    """
    if not customer_user:
        return {"error": "You must be logged in as a customer to use this tool."}
    
    orders = Order.objects.filter(customer=customer_user).select_related("rider").order_by("-created_at")[:10]
    
    results = []
    for o in orders:
        results.append({
            "order_id": o.id,
            "receipt_token": o.receipt_token,
            "status": o.get_status_display(),
            "payment_status": o.get_payment_status_display(),
            "total_amount": float(o.total_amount),
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    return {
        "orders": results,
        "count": len(results),
        "message": "Listed your recent orders." if results else "You have no placed orders yet."
    }

# ─────────────────────────────────────────────────────────────────
#  EMPLOYEE TOOLS
# ─────────────────────────────────────────────────────────────────

def _resolve_period(period: str):
    """Return a (start_dt, label) tuple from a period string."""
    now = timezone.now()
    period = (period or "today").lower().strip()
    if period in ("today", "day"):
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, "Today"
    elif period in ("week", "this week"):
        start = now - datetime.timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, "This Week"
    elif period in ("month", "this month"):
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, "This Month"
    else:
        # default: today
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, "Today"


def get_today_queue() -> dict:
    """Return today's order counts grouped by status."""
    today = timezone.now().date()
    orders = Order.objects.filter(created_at__date=today)
    status_counts = {
        label: orders.filter(status=code).count()
        for code, label in Order.StatusChoices.choices
    }
    total = orders.count()
    active = orders.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).count()
    return {
        "date": str(today),
        "total_orders_today": total,
        "active_orders": active,
        "by_status": status_counts,
    }


def get_processing_counts() -> dict:
    """Return counts for orders currently at shop or being processed."""
    at_shop = Order.objects.filter(status=Order.StatusChoices.AT_SHOP).count()
    processing = Order.objects.filter(status=Order.StatusChoices.PROCESSING).count()
    return {
        "at_shop": at_shop,
        "processing": processing,
        "total_in_processing_pipeline": at_shop + processing,
    }


def get_walkin_summary() -> dict:
    """Return today's walk-in order summary."""
    today = timezone.now().date()
    walkins = Order.objects.filter(order_type=Order.OrderTypeChoices.WALK_IN, created_at__date=today)
    total = walkins.count()
    paid = walkins.filter(payment_status=Order.PaymentStatusChoices.PAID).count()
    unpaid = walkins.filter(payment_status=Order.PaymentStatusChoices.UNPAID).count()
    completed = walkins.filter(status=Order.StatusChoices.COMPLETED).count()
    active = walkins.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).count()
    revenue = walkins.filter(payment_status=Order.PaymentStatusChoices.PAID).aggregate(t=Sum("total_amount"))["t"] or 0
    return {
        "date": str(today),
        "total_walkin_orders": total,
        "paid": paid,
        "unpaid": unpaid,
        "completed": completed,
        "active": active,
        "collected_revenue": float(revenue),
    }


def lookup_order(identifier: str) -> dict:
    """
    Employee order lookup — accepts receipt token (string) or order ID (numeric).
    """
    identifier = (identifier or "").strip()
    if not identifier:
        return {"error": "Please provide an order ID or receipt token."}

    order = None
    if identifier.isdigit():
        order = Order.objects.select_related("customer", "rider", "employee").filter(id=int(identifier)).first()
    if order is None:
        order = Order.objects.select_related("customer", "rider", "employee").filter(receipt_token=identifier).first()

    if not order:
        return {"error": f"No order found for '{identifier}'."}

    customer_name = None
    if order.customer:
        customer_name = order.customer.get_full_name() or order.customer.username
    elif order.walkin_name:
        customer_name = f"{order.walkin_name} (Walk-in)"

    return {
        "order_id": order.id,
        "receipt_token": order.receipt_token,
        "customer": customer_name,
        "status": order.get_status_display(),
        "order_type": order.get_order_type_display(),
        "payment_status": order.get_payment_status_display(),
        "payment_method": order.get_payment_method_display(),
        "total_amount": float(order.total_amount),
        "rider": (order.rider.username if order.rider else None),
        "employee": (order.employee.username if order.employee else None),
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
    }


def get_unpaid_orders() -> dict:
    """Return all currently unpaid orders (non-cancelled)."""
    unpaid = Order.objects.filter(
        payment_status=Order.PaymentStatusChoices.UNPAID
    ).exclude(
        status=Order.StatusChoices.CANCELLED
    ).select_related("customer").order_by("created_at")[:20]

    results = []
    for o in unpaid:
        results.append({
            "order_id": o.id,
            "customer": o.customer.username if o.customer else o.walkin_name or "Walk-in",
            "status": o.get_status_display(),
            "payment_method": o.get_payment_method_display(),
            "total": float(o.total_amount),
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    return {"unpaid_orders": results, "count": len(results)}


def get_ready_for_delivery() -> dict:
    """Return orders that are ready for delivery or out for delivery."""
    ready = Order.objects.filter(
        status__in=[Order.StatusChoices.READY_FOR_DELIVERY, Order.StatusChoices.OUT_FOR_DELIVERY]
    ).select_related("customer", "rider").order_by("created_at")[:20]

    results = []
    for o in ready:
        results.append({
            "order_id": o.id,
            "customer": o.customer.username if o.customer else o.walkin_name or "Walk-in",
            "status": o.get_status_display(),
            "delivery_address": o.delivery_address or "—",
            "rider": o.rider.username if o.rider else "Unassigned",
            "total": float(o.total_amount),
        })
    return {"ready_for_delivery": results, "count": len(results)}


def get_operational_counts() -> dict:
    """Return current live processing/ready/completed counts."""
    processing = Order.objects.filter(status=Order.StatusChoices.PROCESSING).count()
    at_shop = Order.objects.filter(status=Order.StatusChoices.AT_SHOP).count()
    ready = Order.objects.filter(status=Order.StatusChoices.READY_FOR_DELIVERY).count()
    out = Order.objects.filter(status=Order.StatusChoices.OUT_FOR_DELIVERY).count()
    completed_today = Order.objects.filter(
        status=Order.StatusChoices.COMPLETED,
        updated_at__date=timezone.now().date()
    ).count()
    return {
        "at_shop": at_shop,
        "processing": processing,
        "ready_for_delivery": ready,
        "out_for_delivery": out,
        "completed_today": completed_today,
    }


# ─────────────────────────────────────────────────────────────────
#  ADMIN TOOLS
# ─────────────────────────────────────────────────────────────────

def get_orders_summary(period: str = "today") -> dict:
    """Return total order counts for the given period."""
    start, label = _resolve_period(period)
    orders = Order.objects.filter(created_at__gte=start)
    total = orders.count()
    completed = orders.filter(status=Order.StatusChoices.COMPLETED).count()
    cancelled = orders.filter(status=Order.StatusChoices.CANCELLED).count()
    active = orders.exclude(status__in=[Order.StatusChoices.COMPLETED, Order.StatusChoices.CANCELLED]).count()
    return {
        "period": label,
        "total_orders": total,
        "completed": completed,
        "cancelled": cancelled,
        "active": active,
    }


def get_revenue_summary(period: str = "today") -> dict:
    """Return revenue totals for the given period (paid orders only)."""
    start, label = _resolve_period(period)
    paid = Order.objects.filter(
        created_at__gte=start,
        payment_status=Order.PaymentStatusChoices.PAID
    )
    total_revenue = paid.aggregate(t=Sum("total_amount"))["t"] or 0
    count = paid.count()
    avg = (float(total_revenue) / count) if count > 0 else 0
    return {
        "period": label,
        "total_revenue": float(total_revenue),
        "paid_orders": count,
        "average_order_value": round(avg, 2),
    }


def get_payment_breakdown(period: str = "today") -> dict:
    """Return payment method breakdown for the given period."""
    start, label = _resolve_period(period)
    paid = Order.objects.filter(
        created_at__gte=start,
        payment_status=Order.PaymentStatusChoices.PAID
    )
    cash = paid.filter(payment_method=Order.PaymentMethodChoices.CASH)
    gcash = paid.filter(payment_method=Order.PaymentMethodChoices.GCASH)
    paypal = paid.filter(payment_method=Order.PaymentMethodChoices.PAYPAL)

    def _agg(qs):
        return {
            "count": qs.count(),
            "total": float(qs.aggregate(t=Sum("total_amount"))["t"] or 0),
        }

    return {
        "period": label,
        "cash": _agg(cash),
        "gcash": _agg(gcash),
        "paypal": _agg(paypal),
    }


def get_analytics_summary(period: str = "today") -> dict:
    """Return a full analytics summary combining orders, revenue, and payment breakdown."""
    return {
        "orders": get_orders_summary(period),
        "revenue": get_revenue_summary(period),
        "payments": get_payment_breakdown(period),
    }


# ─────────────────────────────────────────────────────────────────
#  TOOL REGISTRY — maps role → allowed function names
# ─────────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "ANONYMOUS": {
        "faq": faq,
        "estimate_price": estimate_price,
        "get_all_services": get_all_services,
    },
    "CUSTOMER": {
        "faq": faq,
        "estimate_price": estimate_price,
        "get_all_services": get_all_services,
        "track_order": track_order,
        "get_my_orders": get_my_orders,
    },
    "EMPLOYEE": {
        "faq": faq,
        "estimate_price": estimate_price,
        "get_all_services": get_all_services,
        "track_order": track_order,
        "get_my_orders": get_my_orders,
        "get_today_queue": get_today_queue,
        "get_processing_counts": get_processing_counts,
        "get_walkin_summary": get_walkin_summary,
        "lookup_order": lookup_order,
        "get_unpaid_orders": get_unpaid_orders,
        "get_ready_for_delivery": get_ready_for_delivery,
        "get_operational_counts": get_operational_counts,
    },
    "ADMIN": {
        "faq": faq,
        "estimate_price": estimate_price,
        "get_all_services": get_all_services,
        "track_order": track_order,
        "get_my_orders": get_my_orders,
        "get_today_queue": get_today_queue,
        "get_processing_counts": get_processing_counts,
        "get_walkin_summary": get_walkin_summary,
        "lookup_order": lookup_order,
        "get_unpaid_orders": get_unpaid_orders,
        "get_ready_for_delivery": get_ready_for_delivery,
        "get_operational_counts": get_operational_counts,
        "get_orders_summary": get_orders_summary,
        "get_revenue_summary": get_revenue_summary,
        "get_payment_breakdown": get_payment_breakdown,
        "get_analytics_summary": get_analytics_summary,
    },
}
