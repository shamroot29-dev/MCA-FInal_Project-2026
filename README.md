# AI Based Pharmacy System

AI Based Pharmacy System is a Django-based online pharmacy supply workflow for suppliers and chemists. It supports supplier stock management, chemist medicine ordering, order approval, Razorpay test/demo payment, invoice PDF generation, received stock tracking, and AI-based demand forecasting from generated bill history.

## Main Features

### Supplier Portal

- Supplier registration and login.
- Supplier dashboard with related chemists only.
- Add and update medicine stock.
- Supplier-wise stock with quantity, rate, and net price.
- AI smart stock insight for demand, suggested stock, and reorder status.
- View chemist order requests.
- Accept or deny medicine orders.
- Generate professional invoice PDF.
- Generated bill history with chemist, medicine, quantity, amount, and payment status.
- AI demand forecasting page based on generated bill history.

### Chemist Portal

- Chemist registration and login.
- Professional form validation with red error text.
- Select supplier before ordering medicine.
- Quantity restriction based on available supplier stock.
- Payment option while ordering:
  - Pay now through Razorpay Test Mode or local demo payment.
  - Pay later after supplier billing or after receiving medicines.
- Order list with order status and payment status.
- Dashboard with generated bill links.
- Received stock page showing billed medicines.
- Bill detail and PDF download option.
- Medicine guide/search page.

### Payment Flow

- Razorpay Test Mode is supported when test keys are configured.
- Local demo payment is available for project presentation when Razorpay keys are not configured.
- Orders can remain `Pending` for payment.
- Supplier can accept unpaid orders and generate bills.
- Chemist can complete pending payment later.
- Bill and dashboard show whether payment is pending or paid.

### AI Features

- AI demand prediction uses generated bill history.
- If enough monthly history exists, the system uses a trend-based regression approach.
- If history is limited, it uses average monthly demand fallback.
- Stock page shows prediction, suggested stock, stock gap, confidence, and reorder status.

## Technology Stack

- Python 3.10 recommended
- Django 3.1
- SQLite for local/demo database
- HTML, CSS, Bootstrap, JavaScript, jQuery
- pandas, numpy, scikit-learn for prediction logic
- Plotly for prediction graph
- Razorpay Python SDK for payment test mode
- xhtml2pdf for invoice PDF generation

## Project Structure

```text
pharmacy/
|-- Uphar/                     # Main Django project settings and URLs
|-- User_Master/               # Supplier/user portal, stock, bills, AI prediction
|-- Chemist_Master/            # Chemist portal, orders, payments, received stock
|-- guide/                     # Medicine guide/search data
|-- med/                       # Legacy medicine CRUD/search module
|-- reports/                   # Generated project report files
|-- manage.py
|-- requirements.txt
|-- PROJECT_SETUP.md
`-- db.sqlite3                 # Local demo SQLite database, if included
```

## Mail/OTP Integration Status

Email sending is integrated for forgot-password OTP flows.

- Supplier/user forgot password: `User_Master/views.py`
- Chemist forgot password: `Chemist_Master/views.py`
- Library used: Python `smtplib` with Gmail SMTP SSL
- SMTP server: `smtp.gmail.com`
- Port: `465`
- Environment variables:
  - `UPHAR_EMAIL_USER`
  - `UPHAR_EMAIL_PASSWORD`

If these email variables are not configured, the project does not fail. It shows a demo OTP using Django messages, which is useful for local presentation.

For Gmail, use an App Password, not your normal Gmail password.

## Important GitHub Security Note

Do not push real secrets to GitHub.

This project reads `.env` automatically from the project root, but `.env` is ignored by `.gitignore`. Keep it local only.

Before pushing publicly:

- Make sure `.env` is not committed.
- Do not commit real Razorpay keys, email passwords, app passwords, or production secret keys.
- If any key was exposed in a public repository, rotate/regenerate that key from the provider dashboard.

## Environment Variables

Create a `.env` file in the project root for local configuration:

```env
DJANGO_SECRET_KEY=change-this-for-production
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

UPHAR_EMAIL_USER=your-gmail@example.com
UPHAR_EMAIL_PASSWORD=your-gmail-app-password

RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

Email and Razorpay variables are optional for local demo. Without email variables, demo OTP is shown on screen. Without Razorpay variables, local demo payment still works.

## How to Run After Cloning from GitHub

### 1. Clone the repository

```powershell
git clone <your-github-repository-url>
cd pharmacy
```

Use the folder that contains `manage.py`.

### 2. Create a virtual environment

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\activate
```

For macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure `.env`

Create `.env` in the same folder as `manage.py`.

Minimum local demo `.env`:

```env
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Optional payment/email demo:

```env
UPHAR_EMAIL_USER=your-gmail@example.com
UPHAR_EMAIL_PASSWORD=your-gmail-app-password
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

### 5. Apply database migrations

```powershell
python manage.py migrate
```

If `db.sqlite3` is included in the repository, it may already contain demo data. If it is not included, migrations will create a fresh empty database.

### 6. Create Django admin user, optional

```powershell
python manage.py createsuperuser
```

### 7. Run the development server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## Main URLs

```text
/                              Public home page
/signin/                       Supplier login
/signup/                       Supplier registration
/adminDashboard/               Supplier dashboard
/viewstock/                    Supplier stock and AI insight
/addstock/                     Add supplier medicine stock
/Confirm_Orders/               Supplier confirmed orders
/createGraph/                  AI demand forecast

/Chemist_Master/signin/        Chemist login
/Chemist_Master/signup/        Chemist registration
/Chemist_Master/               Chemist home
/Chemist_Master/order-medicine/ Medicine order page
/Chemist_Master/productlist/   Chemist order list
/Chemist_Master/received-stock/ Received stock
/Chemist_Master/dashboard/     Chemist dashboard and bills
/Chemist_Master/Uploaded_Medi/ Medicine guide/search
```

## Recommended Demo Flow

1. Start the server.
2. Register or login as a supplier.
3. Add medicines from `Add Stock`.
4. Register or login as a chemist.
5. Open `Order Medicine`.
6. Select supplier, medicine, quantity, request date, and payment option.
7. Submit the order.
8. Login as supplier and open dashboard/order request.
9. Accept the order.
10. Generate invoice PDF.
11. Login as chemist and open dashboard or received stock.
12. View/download generated bill PDF.
13. Complete pending payment if payment status is pending.
14. Open AI Forecast from supplier portal to show prediction.

## Razorpay Test Mode

1. Create or login to Razorpay Dashboard.
2. Switch to Test Mode.
3. Generate test `Key Id` and `Key Secret`.
4. Add them to `.env`:

```env
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

5. Restart the Django server.

If Razorpay order creation fails or keys are missing, use local demo payment for project presentation.

## Email OTP Setup

For Gmail OTP sending:

1. Enable 2-Step Verification on the Gmail account.
2. Generate a Gmail App Password.
3. Add this to `.env`:

```env
UPHAR_EMAIL_USER=your-gmail@example.com
UPHAR_EMAIL_PASSWORD=your-gmail-app-password
```

4. Restart the Django server.

If these variables are missing, the forgot-password flow displays `Demo OTP` on the page through Django messages.

## Database Notes

The project uses SQLite for local demo:

```text
db.sqlite3
```

For a fresh cloned project:

```powershell
python manage.py migrate
```

If you need demo prediction data, generate bills through the supplier workflow or use an existing demo `db.sqlite3`.

For production, use PostgreSQL or MySQL and configure `DATABASES` in `Uphar/settings.py`.

## Static and Media Files

Static files are served by Django in development mode.

Uploaded files, such as chemist certificates, are stored in:

```text
media/
```

`media/` is ignored in Git because uploaded files are runtime data.

## Troubleshooting

### Module not found

Make sure the virtual environment is activated and dependencies are installed:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Database table missing

Run:

```powershell
python manage.py migrate
```

### Payment does not open Razorpay

Check `.env`:

```env
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

Restart the server after changing `.env`.

### Email OTP is not being sent

Check:

- `UPHAR_EMAIL_USER`
- `UPHAR_EMAIL_PASSWORD`
- Gmail App Password
- Internet connection

If not configured, use the displayed demo OTP.

### Port already in use

Run on another port:

```powershell
python manage.py runserver 127.0.0.1:8001
```

## Production Checklist

- Set `DEBUG = False`.
- Configure `DJANGO_SECRET_KEY`.
- Configure `DJANGO_ALLOWED_HOSTS`.
- Use PostgreSQL/MySQL instead of SQLite.
- Use HTTPS.
- Keep `.env` outside Git.
- Configure production static/media serving.
- Rotate any key that was accidentally exposed.
- Add proper logging and backup strategy.

## Project Report

Generated report files are available in:

```text
reports/
```

The latest TOC-based project report generated for submission is:

```text
reports/AI_Based_Pharmacy_System_Project_Report_Final_TOC.docx
```

## Educational Note

This is an academic/demo project for an MCA final project. Before using it in a real pharmacy business, add production-grade security, validation, testing, deployment hardening, audit logs, and legal/compliance review.
