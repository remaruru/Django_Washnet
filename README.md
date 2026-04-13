# Washnet — Complete Laundry Management System 🧺

Washnet is a comprehensive **Laundry Point-of-Sale (POS) and Management Web Application** built with the Django Web Framework. It facilitates the entire laundry lifecycle—from customer booking (drop-off, walk-in, or delivery) through shop processing, rider delivery, and administrative oversight. The system features role-based access control with distinct dashboards and workflows for Admins, Employees, Riders, and Customers.

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| **10-Stage Order Tracking** | Real-time progress monitoring from creation to completion |
| **Role-Based Access Control** | Distinct workflows for Customers, Employees, Riders, and Admins |
| **Load-based Pricing Engine** | Costs calculated by weight (max 7 kg/load) and service type |
| **AI-Powered Chatbot** | Google Gemini API with role-specific tools and function calling |
| **Weather Forecast Integration** | 7-day forecast suggests optimal laundry days to customers |
| **Secure QR Code Receipts** | 12-character alphanumeric tokens prevent unauthorized access |
| **Google OAuth Login** | One-tap sign-in for customers via Google account |
| **Admin OTP Authentication** | Email-based one-time password required for admin login |
| **Real-time Queue & Dashboard** | Live shop monitoring and status progression metrics |
| **Payments** | Cash and GCash (admin verification required) |
| **Mobile Responsive UI** | Claymorphism / glassmorphism design, fully optimized for portrait mobile |

---

## 🛠️ Technical Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Django 6.0.1 + Django REST Framework |
| **Database** | SQLite (Development) / PostgreSQL (Production) |
| **Frontend** | Django Templates (HTML / CSS / JS) + Chart.js |
| **Artificial Intelligence** | Google Generative AI (Gemini 2.5 Flash) |
| **Google OAuth** | Google API Python Client (`google-api-python-client`) |
| **Cloud & Media** | Cloudinary (image/QR storage) |
| **Email (Transactional)** | Brevo HTTP API (production) / Console backend (development) |
| **Deployment & Server** | Gunicorn + Whitenoise on Render |

---

## 👥 User Roles & Detailed Workflows

### 1. 🛒 Customer
**Primary Goal:** Place orders, manage loads, and track laundry progress.
- **Dashboard & Weather:** View a 7-day weather forecast suggesting optimal days for laundry.
- **Google OAuth Login:** Sign in instantly with an existing Google account. New OAuth users are redirected to a profile-completion page to finish registration.
- **Order Creation (`/customer-create-order/`):** Create Drop-off or Delivery orders. Group laundry into distinct "Loads" (up to 7 kg each). Attach per-piece products (Detergent, Fabric Conditioner) to specific loads.
- **Appointments:** Schedule future pickup dates that shop employees or riders can process later.
- **Tracking System:** Real-time 5-step visual tracking GUI. Uses QR-driven secure tokens to verify status.
- **Analytics & AI:** Utilize the Gemini chatbot for price estimations and order timeline checking.

### 2. 🏪 Employee (Shop Operations)
**Primary Goal:** Process physical laundry loads on-site and run the POS system.
- **Live Queue Monitoring:** View Active, Unassigned, and Shared orders. Tab-based UI (Central, Walk-in, Completed).
- **POS System (`/pos/`):** Dedicated terminal for walk-in customers. Dynamic, API-based customer lookup; assigns ownership automatically for walk-in transactions.
- **Status Progression:** Process orders from `AT_SHOP` → `PROCESSING` → `READY_FOR_DELIVERY`. Cannot bypass delivery-specific statuses.
- **Operations Dashboard:** Track personal processing counts vs shop-wide metrics.

### 3. 🛵 Rider (Logistics & Delivery)
**Primary Goal:** Deliver out-for-delivery packages and execute customer pickups.
- **Job Claiming:** View global `PENDING_ACCEPTANCE` logistics tasks. Click to claim, moving status to `RIDER_ACCEPTED`.
- **Pickup Phase:** `RIDER_ACCEPTED` → `PICKED_UP` → Deliver to shop (`AT_SHOP`).
- **Delivery Phase:** Pick up from shop (`READY_FOR_DELIVERY`) → `OUT_FOR_DELIVERY` → Validate with customer → `COMPLETED`.
- **GPS UI Tools:** Route management with simulated "Live GPS Active" states. Payment collection.

### 4. 👑 Administrator
**Primary Goal:** System oversight, deep analytics, financial security, and staff management.
- **OTP Login Guard:** Admins must verify a one-time password sent to their registered email before accessing the dashboard.
- **OTP Settings (`/admin-dashboard/settings/`):** Admins can update their OTP email, triggering a secondary OTP verification flow.
- **System KPIs Dashboard:** Monitor Total Income, Paid vs Unpaid ratio, and Staff Counts.
- **Analytics Center (`/admin-analytics/`):** Deep statistical charting (Chart.js) for Today, This Week, Month, and Custom Date ranges. Cash vs GCash payment breakdowns.
- **God-View Queue (`/admin-queue/`):** Highly optimized live view of active washing machines without N+1 DB queries.
- **Payment Verification:** Manual approval center for GCash / digital wallet reference numbers. Updates order status to `PAID`.
- **Staff Control (`/admin-users/`):** Direct creation of employee and rider accounts securely.

---

## 🔄 Order Lifecycle (The 10 States)
The backbone of the application runs entirely on sequential state management:

| # | Status | Description |
|---|---|---|
| 1 | `EXPECTING_DROP_OFF` | Customer made external drop-off; shop waiting |
| 2 | `PENDING_ACCEPTANCE` | Waiting for rider claiming mechanism |
| 3 | `RIDER_ACCEPTED` | Logistics locked to specific rider; approaching user |
| 4 | `PICKED_UP` | Rider has collected the clothes |
| 5 | `AT_SHOP` | Arrived at shop; in queue |
| 6 | `PROCESSING` | Employee actively using physical machines |
| 7 | `READY_FOR_DELIVERY` | Shop output finished; logistics phase restart |
| 8 | `OUT_FOR_DELIVERY` | Rider handling final journey |
| 9 | `COMPLETED` | Received and finalized |
| 10 | `CANCELLED` | Terminated transaction |

---

## 💰 Pricing Engine

The system uses dual-metric pricing:

**Services (Per Kg)**
| Service | Price |
|---|---|
| Wash & Dry | ₱100.00 (max 7 kg/load) |
| Wash Only | ₱60.00 |
| Dry Only | ₱50.00 |

**Products (Per Piece)**
| Product | Price |
|---|---|
| Detergent | ₱15.00 |
| Fabric Conditioner | ₱15.00 |

---

## 🤖 AI Chatbot (Gemini) Function Capabilities

The system leverages Google Generative AI with role-aware database tooling:

| Role | Capabilities |
|---|---|
| **Anonymous** | Service cost listings, operations info, FAQ routing |
| **Customer** | Queries DB by token ID to output the exact pipeline queue of specific orders |
| **Employee** | Aggregates shop daily walk-ins vs current live machine usage metrics |
| **Admin** | Direct data feeds linking to financial metrics and tracking values |

---

## 🔐 Security Features

- **Admin OTP Authentication** — Every admin login triggers a time-limited OTP sent via Brevo to the admin's registered email.
- **Google OAuth (Customers)** — Secure OAuth 2.0 flow. New OAuth users complete profile registration before accessing the platform.
- **QR Token Receipts** — 12-character cryptographically random tokens on every order receipt.
- **Production HTTPS Enforcement** — HSTS, secure cookies, and SSL redirect active when `DEBUG=False`.
- **CSRF Protection** — Trusted origins enforced for all form submissions and OAuth callbacks.

---

## ⚙️ Local Development Setup

### 1. Clone & Environment

```bash
git clone https://github.com/remaruru/Django_Washnet.git
cd Django_Washnet
python -m venv venv
```

### 2. Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Database Setup & Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Database (Critical for roles & items)

Initialize standard wash configurations and test accounts:

```bash
python make_dev_items.py
python make_dev_users.py
```

> This creates default accounts: `gelo` (admin), `admin`, `customer`, `employee`, `rider` — with respective permissions mapped instantly.

### 6. Run the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** to view the application.

---

## 🚀 Deployment on Render

The project is configured to deploy on **[Render](https://render.com/)** (Free Tier) using a managed PostgreSQL database and a Python web service.

### Services Provisioned

| Service | Name | Plan | Type |
|---|---|---|---|
| Web App | `washnet-pos` | Free | Python (Gunicorn) |
| Database | `washnet-db` | Free | PostgreSQL |

---

### `render.yaml` — Infrastructure as Code

The `render.yaml` at the root defines the full infrastructure declaratively:

```yaml
services:
  - type: web
    name: washnet-pos
    runtime: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn laundry_pos.wsgi:application"
    plan: free
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: DATABASE_URL
        fromDatabase:
          name: washnet-db
          property: connectionString
      - key: GEMINI_API_KEY
        sync: false
      - key: GOOGLE_OAUTH_CLIENT_ID
        sync: false
      - key: GOOGLE_OAUTH_CLIENT_SECRET
        sync: false
      - key: GOOGLE_OAUTH_REDIRECT_URI
        sync: false
      - key: RENDER_EXTERNAL_URL
        sync: false

databases:
  - name: washnet-db
    plan: free
    databaseName: washnet
    user: washnet_user
```

---

### `build.sh` — Automated Build Script

Every deploy on Render runs this script:

```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python make_dev_users.py
python make_dev_items.py
```

---

### Environment Variables

Set the following in the **Render Dashboard → Environment**:

| Variable | Description | How Set |
|---|---|---|
| `SECRET_KEY` | Django secret key | Auto-generated by Render |
| `DEBUG` | Set to `False` for production | Defined in `render.yaml` |
| `DATABASE_URL` | PostgreSQL connection string | Auto-linked from `washnet-db` |
| `CLOUDINARY_URL` | Cloudinary connection string | Set manually |
| `GEMINI_API_KEY` | Google Gemini AI API key | Set manually |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID | Set manually |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret | Set manually |
| `GOOGLE_OAUTH_REDIRECT_URI` | OAuth callback URL (e.g. `https://your-app.onrender.com/oauth/google/callback/`) | Set manually |
| `BREVO_API_KEY` | Brevo email API key for Admin OTP emails | Set manually |
| `RENDER_EXTERNAL_URL` | Auto-set by Render; used for CSRF trusted origins | Auto-set by Render |

> ⚠️ All `sync: false` variables must be set manually in the Render dashboard — they are never committed to source control.

---

### Deploy Steps

1. Push your code to GitHub.
2. Connect the repository to Render.
3. Render detects `render.yaml` and provisions the web service + database automatically.
4. Set all required environment variables in the Render dashboard.
5. Trigger a manual deploy or push to `main` — Render runs `build.sh` and starts Gunicorn.
