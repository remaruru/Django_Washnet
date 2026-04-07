# Washnet - Complete Laundry Management System 🧺

Washnet is a comprehensive Laundry Point-of-Sale (POS) and Management Web Application built with the Django Web Framework. It facilitates the entire laundry lifecycle from customer booking (drop-off, walk-in, or delivery) to shop processing, rider delivery, and administrative oversight. The system features role-based access control with distinct dashboards and workflows for Admins, Employees, Riders, and Customers.

## 🌟 Key Features
- **10-Stage Order Status Tracking**: Real-time progress monitoring from creation to completion.
- **Role-Based Access Control (RBAC)**: Distinct workflows for Customers, Employees, Riders, and Admins.
- **Load-based Pricing Engine**: Calculates costs based on weight (max 7kg per physical load) and service type.
- **AI-Powered Chatbot**: Google Gemini API powered customer support with role-specific tools and function calling.
- **Weather Forecast Integration**: Suggests optimal laundry days to customers based on real-time weather.
- **Secure QR Code Receipts**: Uses 12-character alphanumeric tokens preventing unauthorized access.
- **Real-time Queue & Dashboard**: Live shop monitoring and status progression metrics.
- **Payments**: Cash, GCash (admin verification required), and PayPal integration.
- **Mobile Responsive & Claymorphism UI**: Beautiful, engaging UI with glassmorphism effects.

---

## 🛠️ Technical Stack
- **Backend Framework**: Django 6.0.1 with Django REST Framework
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Frontend**: Django Templates (HTML/CSS/JS) with Chart.js
- **Artificial Intelligence**: Google Generative AI (Gemini 2.5 Flash Lite)
- **Cloud & Media**: Cloudinary (Image/QR storage)
- **Deployment & Server**: Gunicorn, Whitenoise, Nginx

---

## 👥 User Roles & Detailed Workflows

### 1. 🛒 Customer
**Primary Goal:** Place orders, manage loads, and track laundry progress.
- **Dashboard & Weather:** View a 7-day weather forecast suggesting optimal days for laundry.
- **Order Creation (`/customer-create-order/`):** Create Drop-off or Delivery orders. Group laundry into distinct "Loads" (up to 7kg each). Attach per-piece products (Detergent, Fabric Conditioner) to specific loads.
- **Appointments:** Schedule future pickup dates that shop employees or riders can process later.
- **Tracking System:** Real-time 5-step visual tracking GUI. Uses QR-driven secure tokens to verify status.
- **Analytics & AI:** Utilize the Gemini chatbot for price estimations and order timeline checking.

### 2. 🏪 Employee (Shop Operations)
**Primary Goal:** Process physical laundry loads on-site and run the POS system.
- **Live Queue Monitoring:** View Active, Unassigned, and Shared orders. Tab-based UI (Central, Walk-in, Completed).
- **POS System (`/pos/`):** Dedicated terminal interface to walk-in new customers. Dynamic, API-based customer lookup. Assigns ownership automatically for walk-in transactions.
- **Status Progression:** Process orders from `AT_SHOP` → `PROCESSING` → `READY_FOR_DELIVERY`. Cannot bypass delivery-specific statuses.
- **Operations Dashboard:** Track personal processing counts vs shop-wide metrics.

### 3. 🛵 Rider (Logistics & Delivery)
**Primary Goal:** Deliver out-for-delivery packages and execute customer pickups.
- **Job Claiming:** View global `PENDING_ACCEPTANCE` logistics tasks. Click to claim, moving status to `RIDER_ACCEPTED`.
- **Pickup Phase:** `RIDER_ACCEPTED` → `PICKED_UP` → Deliver to shop (`AT_SHOP`).
- **Delivery Phase:** Pick up from shop (`READY_FOR_DELIVERY`) → `OUT_FOR_DELIVERY` → Validate with customer → `COMPLETED`.
- **GPS UI Tools:** Route management with simulated "Live GPS Active" states. Payment collection.

### 4. 👑 Administrator
**Primary Goal:** System oversight, deep analytics, and financial security.
- **System KPIs Dashboard:** Monitor Total Income, Paid VS Unpaid ratio, Staff Counts.
- **Analytics Center (`/admin-analytics/`):** Deep statistical charting (Chart.js) with views for Today, This Week, Month, and Custom Dates. Breeds metrics on payment formats (Cash vs GCash vs PayPal).
- **God-View Queue (`/admin-queue/`):** Highly optimized live track of the active washing machines without hitting N+1 DB locks. 
- **Payment Verification:** Manual approval center for GCash / digital wallet reference numbers. Updates order natively to `PAID`.
- **Staff Control (`/admin-users/`):** Direct creation of employee and rider accounts securely.

---

## 🔄 Order Lifecycle (The 10 States)
The backbone of the application runs entirely on sequential state management:

1. **EXPECTING_DROP_OFF** - Customer made external drop-off, shop waiting.
2. **PENDING_ACCEPTANCE** - Waiting for Rider claiming mechanism.
3. **RIDER_ACCEPTED** - Logistics locked to specific rider, approaching user.
4. **PICKED_UP** - Rider attained clothes.
5. **AT_SHOP** - Arrived at shop, queue phase.
6. **PROCESSING** - Employee actively using physical machines.
7. **READY_FOR_DELIVERY** - Shop output finished, logistics phase restart.
8. **OUT_FOR_DELIVERY** - Rider handling final journey.
9. **COMPLETED** - Received and finalized.
10. **CANCELLED** - Terminated transaction.

---

## 💰 Pricing Engine Configurator
The system uses dual-metric pricing:
- **Services (Per Kg)**:
  - Wash & Dry: ₱100.00 (Max 7kg limit)
  - Wash Only: ₱60.00
  - Dry Only: ₱50.00
- **Products (Per Piece)**:
  - Detergent: ₱15.00
  - Fabric Conditioner: ₱15.00

---

## 🤖 AI Chatbot (Gemini) Function Capabilities
The system leverages Google Generative AI connected dynamically with database tooling:
- **Anonymous Users**: Returns service cost listings, operations, FAQ routing.
- **Customers**: Queries db by "token ID" to output the exact pipeline queue of specific orders.
- **Employees**: Aggregates the shop's total day "walk-ins" vs current live machine usage processing metrics.
- **Admins**: Direct data feeds linking to the site's financial metrics and tracking values natively.

---

## ⚙️ Local Development Setup

### 1. Clone & Environment Strategy
```bash
git clone https://github.com/remaruru/Django_Washnet.git
cd Django_Washnet
python -m venv venv
```

### 2. Activate Virtual Shell
```bash
# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate
```

### 3. Install Core Requirements
```bash
pip install -r requirements.txt
```

### 4. Database Setup & Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Database Data (Critical for Role functionality & Items)
Initialize standard wash configurations and test accounts:
```bash
python make_dev_items.py
python make_dev_users.py
```
*Note: this creates default accounts (gelo, admin, customer, employee, rider) with respective permissions mapped instantly.*

### 6. Run Server Environment
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/ to view the application!

---

## 📊 Deployment Prep (Render)
The system is built mapped naturally for Render automated hosting. Key scripts:
1. Built-in `build.sh` manages requirements execution, static collections mapping (`whitenoise`), and environment execution triggers.
2. Production relies natively on PostgreSQL configuration setup injected entirely into `laundry_pos/settings.py` via `dj-database-url`.
3. Valid WSGI target binding managed with Server-Side processing via `gunicorn`.
