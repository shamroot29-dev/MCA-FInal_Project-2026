# Uphar Pharmacy Management System

## Recommended Environment

- Python 3.10.x
- Django 3.1
- SQLite for local/demo use

## Setup Commands

```powershell
cd D:\pharmacy\pharmacy
py -3.10 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Optional production/demo integrations:

```powershell
$env:UPHAR_EMAIL_USER="your-gmail@example.com"
$env:UPHAR_EMAIL_PASSWORD="your-app-password"
$env:RAZORPAY_KEY_ID="rzp_test_your-key-id"
$env:RAZORPAY_KEY_SECRET="your-test-secret"
```

Open:

```text
http://127.0.0.1:8000/
```

## Main Modules

- Supplier/Admin portal: stock, chemist approval, order confirmation, bill generation, prediction graph
- Chemist portal: chemist registration/login, stock ordering, order status, bill view
- Medicine guide: searchable medicine information and CSV import
- Medicine management: legacy medicine CRUD/search module

## Demo Flow

1. Open the landing page.
2. Login as supplier/admin and review registered chemists.
3. Open stock view and verify stock quantity.
4. Login as chemist and place a stock order.
5. On the payment page, use Razorpay Test Mode if keys are configured, or use Continue Local Demo Payment.
6. Return to supplier/admin dashboard and accept the order.
7. Generate bill PDF from confirmed orders.
8. Login as chemist and open Dashboard or Received Stock to review the billed medicine.
9. Show prediction graph from previous bill records.

## Razorpay Test Mode

Use Razorpay Test Mode keys for the payment demo. In Razorpay Dashboard, switch to Test Mode and copy the test `Key Id` and `Key Secret`.

Set them before starting the server:

```powershell
$env:RAZORPAY_KEY_ID="rzp_test_your-key-id"
$env:RAZORPAY_KEY_SECRET="your-test-secret"
python manage.py runserver
```

If these variables are not set, the payment page still supports `Continue Local Demo Payment` so the full order-to-bill flow can be shown without external setup.

## Notes

- Do not use copied `myenv` or `myenv1`; create `.venv` on every system.
- Email and Razorpay credentials should be configured through environment variables before production use.
- SQLite database is suitable for demo. Use PostgreSQL/MySQL for production.
