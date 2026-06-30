import os

from django.shortcuts import render,redirect,get_object_or_404
from django.http import request,HttpResponseRedirect,HttpResponse
from Chemist_Master.models import *
from med.models import Medicine
from med.forms import MedicineForm
from Chemist_Master.forms import ChemistRegisterform,guideForm
from User_Master.models import UserRegister
from guide.models import guides
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from datetime import date
from email.message import EmailMessage
import random
from difflib import SequenceMatcher
#email
import smtplib, ssl,pandas 
import razorpay
from .models import SK_Bills,ChemistRegister

from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa

from django.http import HttpResponse
from django.views.generic import View
from plotly.offline import plot
from plotly.graph_objs import Scatter

import pdfkit

CHEMIST_SESSION_KEY = 'chemist_user'
ORDER_TOTAL_SESSION_KEY = 'chemist_order_total'
PENDING_ORDER_SESSION_KEY = 'chemist_pending_order'
RAZORPAY_ORDER_SESSION_KEY = 'chemist_razorpay_order_id'
PAID_PAYMENT_STATUSES = ('Demo Paid', 'Razorpay Paid', 'Paid')


def is_payment_paid(payment_status):
    return payment_status in PAID_PAYMENT_STATUSES


def clamp_score(value):
    return max(0, min(100, round(value)))


def medicine_match_score(query, medicine_name):
    if not query:
        return 100
    query_text = query.lower().strip()
    medicine_text = medicine_name.lower().strip()
    if not query_text:
        return 100
    if query_text == medicine_text:
        return 100
    if query_text in medicine_text:
        return 90
    return round(SequenceMatcher(None, query_text, medicine_text).ratio() * 100)


def is_orderable_medicine_match(query, medicine_name):
    if not query:
        return True
    query_text = query.lower().strip()
    medicine_text = medicine_name.lower().strip()
    return query_text == medicine_text or query_text in medicine_text


def supplier_reliability_score(supplier):
    orders = ProductDetails.objects.filter(supplier=supplier)
    bills = SK_Bills.objects.filter(supplier=supplier)
    order_count = orders.count()
    bill_count = bills.count()
    if not order_count and not bill_count:
        return {
            'score': 65,
            'label': 'New supplier history',
            'accepted_orders': 0,
            'bills': 0,
        }

    accepted_orders = orders.filter(status=True).count()
    denied_orders = orders.filter(isDeny=True).count()
    paid_bills = bills.exclude(payment_status='Pending').count()

    accepted_ratio = accepted_orders / order_count if order_count else 0
    denied_ratio = denied_orders / order_count if order_count else 0
    paid_ratio = paid_bills / bill_count if bill_count else 0
    score = 55 + (accepted_ratio * 30) + (paid_ratio * 15) - (denied_ratio * 20)
    score = clamp_score(score)

    if score >= 85:
        label = 'Highly reliable'
    elif score >= 70:
        label = 'Reliable'
    elif score >= 55:
        label = 'Moderate history'
    else:
        label = 'Review before ordering'

    return {
        'score': score,
        'label': label,
        'accepted_orders': accepted_orders,
        'bills': bill_count,
    }


def build_supplier_comparison(stocks, query, requested_qty):
    if not stocks:
        return []

    prices = [float(stock.price) for stock in stocks if stock.price is not None]
    quantities = [int(stock.quantity) for stock in stocks]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else min_price
    reliability_cache = {}
    rows = []

    for stock in stocks:
        supplier = stock.supplier
        if supplier.id not in reliability_cache:
            reliability_cache[supplier.id] = supplier_reliability_score(supplier)
        reliability = reliability_cache[supplier.id]

        price = float(stock.price)
        quantity = int(stock.quantity)
        enough_stock = requested_qty <= quantity
        if max_price == min_price:
            price_score = 100
        else:
            price_score = 100 - ((price - min_price) / (max_price - min_price) * 100)
        stock_score = min(100, (quantity / requested_qty) * 100) if requested_qty else 100
        availability_penalty = 0 if enough_stock else 35
        match_score = medicine_match_score(query, stock.productName)
        total_score = (
            (price_score * 0.35) +
            (stock_score * 0.25) +
            (reliability['score'] * 0.25) +
            (match_score * 0.15) -
            availability_penalty
        )

        rows.append({
            'stock_id': stock.id,
            'supplier_id': supplier.id,
            'supplier_email': supplier.uid,
            'medicine': stock.productName,
            'available_qty': quantity,
            'rate': price,
            'net_price': round(price * requested_qty, 2),
            'requested_qty': requested_qty,
            'enough_stock': enough_stock,
            'score': clamp_score(total_score),
            'price_score': clamp_score(price_score),
            'stock_score': clamp_score(stock_score),
            'match_score': match_score,
            'reliability_score': reliability['score'],
            'reliability_label': reliability['label'],
            'accepted_orders': reliability['accepted_orders'],
            'bill_count': reliability['bills'],
            'badges': [],
        })

    eligible_rows = [row for row in rows if row['enough_stock']]
    scoring_rows = eligible_rows or rows
    if scoring_rows:
        best_price = min(scoring_rows, key=lambda row: row['rate'])
        highest_stock = max(scoring_rows, key=lambda row: row['available_qty'])
        recommended = max(scoring_rows, key=lambda row: row['score'])
        best_price['badges'].append('Best Price')
        highest_stock['badges'].append('Highest Stock')
        recommended['badges'].insert(0, 'Recommended')
        for row in rows:
            if row['reliability_score'] >= 85:
                row['badges'].append('Trusted Supplier')
            if not row['enough_stock']:
                row['badges'].append('Insufficient Qty')

    return sorted(rows, key=lambda row: (row['enough_stock'], row['score'], -row['rate']), reverse=True)


def suggest_similar_medicines(query, stocks):
    if not query:
        return []
    ranked = {}
    for stock in stocks:
        score = medicine_match_score(query, stock.productName)
        current = ranked.get(stock.productName)
        if current is None or score > current:
            ranked[stock.productName] = score
    return [
        name for name, score in sorted(ranked.items(), key=lambda item: item[1], reverse=True)
        if score >= 60
    ][:6]


def get_order_form_context(username, request):
    suppliers = UserRegister.objects.all().order_by('uid')
    prods = StockDetails.objects.filter(
        supplier__isnull=False,
        quantity__gt=0
    ).select_related('supplier').order_by('supplier__uid', 'productName')
    return {
        'username': username,
        'prods': prods,
        'suppliers': suppliers,
        'selected_supplier': request.GET.get('supplier') or request.POST.get('supplier', ''),
        'selected_product': request.GET.get('product') or request.POST.get('productname', ''),
        'selected_quantity': request.GET.get('quantity') or request.POST.get('productquantity', ''),
        'selected_date': request.GET.get('date') or request.POST.get('data', ''),
    }


def build_otp_email(email_user, recipient_email, otp, account_type):
    message = EmailMessage()
    message['Subject'] = 'Password Recovery OTP - AI Based Pharmacy System'
    message['From'] = f"AI Based Pharmacy System <{email_user}>"
    message['To'] = recipient_email
    message.set_content(f"""Hello,

We received a password recovery request for your {account_type} account in AI Based Pharmacy System.

Your One Time Password (OTP) is:

{otp}

Please enter this OTP on the verification page to continue resetting your password.

If you did not request this password reset, please ignore this email. Your account remains safe.

Regards,
AI Based Pharmacy System Team
""")
    return message

#Chemist signin page
def chemist_signin(request):
    if request.method=="POST":
        print(request.POST.get('cid'))
        try:
            chemist_password = request.POST.get('chemistpwd', '')
            m = ChemistRegister.objects.get(cid__iexact=request.POST.get('cid', '').strip())
            if check_password(chemist_password, m.chemistpwd) or m.chemistpwd == chemist_password:
                request.session[CHEMIST_SESSION_KEY] = m.cid
                if m.chemistpwd == chemist_password:
                    try:
                        m.chemistpwd = make_password(chemist_password)
                        m.save(update_fields=['chemistpwd'])
                    except Exception:
                        messages.warning(request, 'Login successful. Password security upgrade will be retried later.')
                return redirect('chemist:ch_index')
            else:
                messages.error(request, 'Invalid email or password. Please check your login details.')
        except ChemistRegister.DoesNotExist:
            messages.error(request, 'No chemist account found with this email.')
        except Exception:
            messages.error(request, 'Login failed. Please try again.')
    return render(request,'chemist_signin1.html')

# Showing uploaded medicines by chemist
def Uploaded_Medi(request):
    
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        query = request.GET.get('q', '').strip()
        med = guides.objects.all().order_by('mname')
        if query:
            med = med.filter(
                Q(mname__icontains=query) |
                Q(drug__icontains=query) |
                Q(symptoms__icontains=query) |
                Q(diseases__icontains=query)
            )
        query_params = request.GET.copy()
        query_params.pop('page', None)
        paginator = Paginator(med, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request,'test.html',{
            'med': med,
            'page_obj': page_obj,
            'username': username,
            'query': query,
            'query_string': query_params.urlencode(),
            'result_count': med.count(),
        })
    else:
        return redirect('chemist:ch_signin')

            
  # Update medicine {done by chemist}   
def update_med(request,id):
    if CHEMIST_SESSION_KEY in request.session:
        medi = guides.objects.get(id=id)  
        form = guideForm(request.POST or None, instance = medi)  
        if form.is_valid():  
            form.save()  
            return redirect('chemist:Uploaded_Medi')
        return render(request,'edit.html', {'medi': medi}) 
    else:
        return redirect('chemist:ch_signin')
 
# delete medicine{done by chemist}
def delete_med(request,id):
    med = guides.objects.get(id=id)
    med.delete()
    return redirect('chemist:Uploaded_Medi')
    
# Chemist module home page
def chemist_index(request):
    if CHEMIST_SESSION_KEY in request.session:
        return render(request, 'chemist_index.html', {'username': request.session[CHEMIST_SESSION_KEY]})
    else:
        return redirect('chemist:ch_signin')
        
# chemist signup
def chemist_signup(request):
    obj=ChemistRegisterform(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None
    )
    if obj.is_valid():
        chemist = obj.save(commit=False)
        chemist.chemistpwd = make_password(chemist.chemistpwd)
        chemist.save()
        messages.success(request, 'Chemist account created successfully. Please sign in.')
        return redirect('chemist:ch_signin')
    elif request.method == 'POST':
        messages.error(request, 'Please correct the highlighted signup details.')
    return render(request,'chemist_signup.html',{'obj':obj})

#chemist logout
def logout(request):
    if CHEMIST_SESSION_KEY in request.session:
        del request.session[CHEMIST_SESSION_KEY]
        return redirect('chemist:ch_signin')
    else:
        return redirect('chemist:ch_signin')
#chemist forgotpassword

def forgot_pass(request):
    email = request.POST.get('email', '').strip()
    if not email:
        return render(request,'email.html')

    if not ChemistRegister.objects.filter(cid__iexact=email).exists():
        request.session.pop('username', None)
        request.session.pop('otp', None)
        messages.error(request, 'This email is not registered as a chemist. Please use your registered email address.')
        return render(request, 'email.html', {'email': email})

    request.session['username'] = email
    otp = ''
    rand = random.choice('0123456789')
    rand1 = random.choice('0123456789')
    rand2 = random.choice('0123456789')
    rand3 = random.choice('0123456789')
    otp = rand + rand1 + rand2 + rand3
    request.session['otp'] = otp


    email_user = os.environ.get('UPHAR_EMAIL_USER', '').strip()
    email_password = os.environ.get('UPHAR_EMAIL_PASSWORD', '').replace(' ', '').strip()
    if email_user and email_password:
        try:
            port = 465
            context = ssl.create_default_context()
            message = build_otp_email(email_user, email, otp, 'chemist')
            server = smtplib.SMTP_SSL("smtp.gmail.com",port,context=context)
            server.login(email_user,email_password)
            server.send_message(message)
            server.quit()
            messages.success(request, 'OTP has been sent to your email.')
        except smtplib.SMTPAuthenticationError:
            messages.warning(request, f"Email authentication failed. Demo OTP: {otp}")
        except Exception:
            messages.warning(request, f"Email could not be sent. Demo OTP: {otp}")
    else:
        messages.warning(request, f"Demo OTP: {otp}")
    return redirect('chemist:otpcheck')
    return render(request,'email.html')

def otpcheck(request):
    if 'otp' not in request.session:
        messages.error(request, 'OTP session expired. Please request a new OTP.')
        return redirect('chemist:forgotpass')

    otp = request.session['otp']
    if request.method == 'POST':
        otpobj = request.POST.get('otp', '').strip()
        if otp == otpobj:
            return redirect('chemist:newpassword')
        messages.error(request, 'Wrong OTP entered. Please check the OTP and try again.')
        return render(request, 'otp.html', {'otp': otpobj})
    return render(request,'otp.html')

def newpassword(request):
    new_pass = request.POST.get('password')
    if request.method == 'POST':
        obj = ChemistRegister.objects.get(cid = request.session['username'])
        obj.chemistpwd = make_password(new_pass)
        obj.save()
        return redirect('chemist:ch_signin')
    return render(request,'forgotpassword.html')

def save_pending_order(request, payment_status):
    pending_order = request.session.get(PENDING_ORDER_SESSION_KEY)
    username = request.session.get(CHEMIST_SESSION_KEY)
    if not pending_order or not username:
        return None

    store = ChemistRegister.objects.get(cid=username)
    stock = StockDetails.objects.get(id=int(pending_order['product_id']))
    supplier = UserRegister.objects.get(id=int(pending_order['supplier_id']))
    if stock.supplier_id != supplier.id:
        raise ValueError('Selected medicine does not belong to the selected supplier.')
    if int(pending_order['quantity']) > stock.quantity:
        raise ValueError(f"Only {stock.quantity} units of {stock.productName} are available.")
    order = ProductDetails()
    order.supplier = supplier
    order.store_person = store
    order.productname = stock.productName
    order.productquantity = int(pending_order['quantity'])
    order.date = pending_order['date']
    order.payment_status = payment_status
    order.save()

    request.session.pop(PENDING_ORDER_SESSION_KEY, None)
    request.session.pop(ORDER_TOTAL_SESSION_KEY, None)
    request.session.pop(RAZORPAY_ORDER_SESSION_KEY, None)
    request.session.modified = True
    return order


def get_order_amount(order):
    stock = StockDetails.objects.filter(
        supplier=order.supplier,
        productName=order.productname
    ).first()
    rate = stock.price if stock else 0
    return float(rate) * int(order.productquantity), rate

def create_razorpay_order(amount):
    key_id = os.environ.get('RAZORPAY_KEY_ID')
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
    if not key_id or not key_secret:
        return None

    client = razorpay.Client(auth=(key_id, key_secret))
    return client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': '1'
    })


def render_payment_page(request, amount, order_summary, title, text):
    donationAmount = int(float(amount) * 100)
    razorpay_order = None
    razorpay_error = ''
    if os.environ.get('RAZORPAY_KEY_ID') and os.environ.get('RAZORPAY_KEY_SECRET') and donationAmount > 0:
        try:
            razorpay_order = create_razorpay_order(donationAmount)
            request.session[RAZORPAY_ORDER_SESSION_KEY] = razorpay_order['id']
            request.session.modified = True
        except Exception:
            razorpay_error = 'Razorpay test order could not be created. You can continue with local demo payment.'
    return render(request, 'payment.html', {
        "donationAmount": donationAmount,
        "displayAmount": float(amount),
        "order": order_summary,
        "payment_title": title,
        "payment_text": text,
        "razorpay_key_id": os.environ.get('RAZORPAY_KEY_ID', ''),
        "razorpay_order_id": razorpay_order['id'] if razorpay_order else '',
        "razorpay_error": razorpay_error,
        "username": request.session.get(CHEMIST_SESSION_KEY, ''),
    })


def verify_payment_submission(request):
    key_id = os.environ.get('RAZORPAY_KEY_ID')
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
    if request.POST.get('demo_payment') == '1' or not key_id or not key_secret:
        return 'Demo Paid'

    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id') or request.session.get(RAZORPAY_ORDER_SESSION_KEY)
    razorpay_signature = request.POST.get('razorpay_signature')
    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        messages.error(request, 'Payment was not completed. Please try again.')
        return None
    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except Exception:
        messages.error(request, 'Razorpay payment verification failed. Please try again or use demo payment.')
        return None
    return 'Razorpay Paid'

def order_medicine(request):
    if CHEMIST_SESSION_KEY in request.session:

        username = request.session[CHEMIST_SESSION_KEY]
        context = get_order_form_context(username, request)
        if request.POST:
            try:
                supplier_id = int(request.POST['supplier'])
                supplier = UserRegister.objects.get(id=supplier_id)
                pro_data = int(request.POST['productname'])
                pro_qty = int(request.POST['productquantity'])
                prod_date = request.POST['data']
                pro_nm = StockDetails.objects.get(id=pro_data, supplier=supplier, quantity__gt=0)
            except (KeyError, ValueError, UserRegister.DoesNotExist, StockDetails.DoesNotExist):
                messages.error(request, 'Please select a valid supplier, medicine, and quantity.')
                return render(request, 'store/addproduct.html', context)

            if pro_qty <= 0 or pro_qty > 500:
                messages.error(request, 'Quantity should be between 1 and 500.')
                return render(request, 'store/addproduct.html', context)

            if pro_qty > pro_nm.quantity:
                messages.error(request, f"Only {pro_nm.quantity} units of {pro_nm.productName} are available.")
                return render(request, 'store/addproduct.html', context)

            if not prod_date:
                messages.error(request, 'Please select a request date.')
                return render(request, 'store/addproduct.html', context)

            total = float(pro_nm.price) * pro_qty
            payment_timing = request.POST.get('payment_timing', 'later')
            request.session[PENDING_ORDER_SESSION_KEY] = {
                'supplier_id': supplier.id,
                'supplier_email': supplier.uid,
                'product_id': pro_nm.id,
                'product_name': pro_nm.productName,
                'quantity': pro_qty,
                'date': prod_date,
                'rate': float(pro_nm.price),
                'total': total,
            }
            request.session[ORDER_TOTAL_SESSION_KEY] = total
            request.session.modified = True
            if payment_timing == 'now':
                messages.info(request, 'Order details are ready. Complete payment to place the request.')
                return redirect('chemist:paymentData')
            try:
                save_pending_order(request, 'Pending')
            except ValueError as exc:
                messages.error(request, str(exc))
                return render(request, 'store/addproduct.html', context)
            messages.success(request, 'Order request placed with payment pending. You can pay before or after supplier billing.')
            return redirect('chemist:ProductListView')
        return render(request, 'store/addproduct.html', context)
    else:
        return redirect('chemist:ch_signin')


def SmartMedicineFinder(request):
    if CHEMIST_SESSION_KEY not in request.session:
        return redirect('chemist:ch_signin')

    username = request.session[CHEMIST_SESSION_KEY]
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'recommended')
    try:
        requested_qty = int(request.GET.get('quantity', '1') or 1)
    except ValueError:
        requested_qty = 1
    requested_qty = max(1, min(requested_qty, 500))

    all_stocks = list(
        StockDetails.objects.filter(
            supplier__isnull=False,
            quantity__gt=0
        ).select_related('supplier').order_by('productName', 'supplier__uid')
    )

    candidate_stocks = []
    suggestions = []
    if query:
        candidate_stocks = [
            stock for stock in all_stocks
            if is_orderable_medicine_match(query, stock.productName)
        ]
        if not candidate_stocks:
            suggestions = suggest_similar_medicines(query, all_stocks)
    else:
        candidate_stocks = all_stocks[:20]

    results = build_supplier_comparison(candidate_stocks, query, requested_qty)

    if sort_by == 'price':
        results = sorted(results, key=lambda row: (not row['enough_stock'], row['rate']))
    elif sort_by == 'stock':
        results = sorted(results, key=lambda row: row['available_qty'], reverse=True)
    elif sort_by == 'reliability':
        results = sorted(results, key=lambda row: row['reliability_score'], reverse=True)

    recommended = results[0] if results else None
    available_suppliers = len({row['supplier_id'] for row in results})
    cheapest_rate = min([row['rate'] for row in results], default=0)
    enough_stock_count = len([row for row in results if row['enough_stock']])

    return render(request, 'store/smart_medicine_finder.html', {
        'username': username,
        'query': query,
        'requested_qty': requested_qty,
        'sort_by': sort_by,
        'results': results,
        'recommended': recommended,
        'suggestions': suggestions,
        'available_suppliers': available_suppliers,
        'cheapest_rate': cheapest_rate,
        'enough_stock_count': enough_stock_count,
        'total_matches': len(results),
    })
    
def paymentData(request):
	if ORDER_TOTAL_SESSION_KEY not in request.session or PENDING_ORDER_SESSION_KEY not in request.session:
		return redirect('chemist:order-medicine')
	if request.method == "POST":
		payment_status = verify_payment_submission(request)
		if not payment_status:
			return redirect('chemist:paymentData')
		try:
			save_pending_order(request, payment_status)
		except ValueError as exc:
			messages.error(request, str(exc))
			return redirect('chemist:order-medicine')
		messages.success(request, 'Payment completed. Order request has been placed.')
		return redirect('chemist:ProductListView')
	return render_payment_page(
		request,
		float(request.session[ORDER_TOTAL_SESSION_KEY]),
		request.session[PENDING_ORDER_SESSION_KEY],
		'Complete payment to place this medicine request.',
		'Pay now through Razorpay Test Mode, or use local demo payment for presentation.'
	)

def paymentComplete(donationAmount, request):
	return paymentData(request)


def PayProductOrder(request, id):
    if CHEMIST_SESSION_KEY not in request.session:
        return redirect('chemist:ch_signin')
    store = ChemistRegister.objects.get(cid=request.session[CHEMIST_SESSION_KEY])
    order = get_object_or_404(ProductDetails, id=id, store_person=store)
    if is_payment_paid(order.payment_status):
        messages.info(request, 'This order payment is already completed.')
        return redirect('chemist:ProductListView')

    amount, rate = get_order_amount(order)
    if request.method == 'POST':
        payment_status = verify_payment_submission(request)
        if not payment_status:
            return redirect('chemist:pay_product_order', id=order.id)
        order.payment_status = payment_status
        order.save(update_fields=['payment_status'])
        request.session.pop(RAZORPAY_ORDER_SESSION_KEY, None)
        messages.success(request, 'Order payment completed successfully.')
        return redirect('chemist:ProductListView')

    return render_payment_page(request, amount, {
        'product_name': order.productname,
        'supplier_email': order.supplier.uid if order.supplier else 'Legacy supplier',
        'quantity': order.productquantity,
        'date': order.date,
        'rate': rate,
        'total': amount,
    }, 'Complete pending payment for this order.', 'Supplier can process unpaid orders, but payment will remain pending until you complete it.')


def PayBill(request, bill_no):
    if CHEMIST_SESSION_KEY not in request.session:
        return redirect('chemist:ch_signin')
    store = ChemistRegister.objects.get(cid=request.session[CHEMIST_SESSION_KEY])
    bills = SK_Bills.objects.filter(Bill_No=bill_no, store_person=store).select_related('supplier')
    if not bills.exists():
        messages.error(request, 'Bill was not found for your account.')
        return redirect('chemist:Dashboard')
    if all(is_payment_paid(bill.payment_status) for bill in bills):
        messages.info(request, 'This bill payment is already completed.')
        return redirect('chemist:SK_View_Bills', ids=bill_no)

    amount = sum(float(bill.pd_tot) for bill in bills)
    first_bill = bills.first()
    if request.method == 'POST':
        payment_status = verify_payment_submission(request)
        if not payment_status:
            return redirect('chemist:pay_bill', bill_no=bill_no)
        bills.update(payment_status=payment_status)
        request.session.pop(RAZORPAY_ORDER_SESSION_KEY, None)
        messages.success(request, 'Bill payment completed successfully.')
        return redirect('chemist:SK_View_Bills', ids=bill_no)

    return render_payment_page(request, amount, {
        'product_name': f'Bill {bill_no}',
        'supplier_email': first_bill.supplier.uid if first_bill.supplier else 'Legacy supplier',
        'quantity': sum(int(bill.pd_qty) for bill in bills),
        'date': first_bill.date_data,
        'rate': 'Mixed',
        'total': amount,
    }, 'Complete pending payment for this generated bill.', 'Use this after supplier billing or after medicines are received.')

def paymentSuccess(request):
	mainMsg = "Thank you for payment"
	return render(request, 'paymentSuccess.html',{'mainHeading':mainMsg})
    
    
def ProductListView(request):
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        store = ChemistRegister.objects.get(cid=username)
        model = ProductDetails.objects.filter(store_person=store).select_related('supplier').order_by('-id')
        return render(request, 'store/productlist.html', {'data': model, 'username': username})
    else:
        return redirect('chemist:ch_signin')

class ReceivedStockSummary():
    def __init__(self, name, quantity, amount, latest_date):
        self.name = name
        self.quantity = quantity
        self.amount = amount
        self.latest_date = latest_date

def ReceivedStockView(request):
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        store = ChemistRegister.objects.get(cid=username)
        bills = SK_Bills.objects.filter(store_person=store).select_related('supplier').order_by('-date_data', '-id')

        summary_map = {}
        for bill in bills:
            item = summary_map.setdefault(bill.pd_nm, {
                'quantity': 0,
                'amount': 0,
                'latest_date': bill.date_data,
            })
            item['quantity'] += bill.pd_qty
            item['amount'] += bill.pd_tot
            if bill.date_data and (item['latest_date'] is None or bill.date_data > item['latest_date']):
                item['latest_date'] = bill.date_data

        summary = [
            ReceivedStockSummary(name, data['quantity'], data['amount'], data['latest_date'])
            for name, data in sorted(summary_map.items())
        ]

        return render(request, 'store/received_stock.html', {
            'username': username,
            'summary': summary,
            'bills': bills,
            'total_quantity': sum(item.quantity for item in summary),
            'total_amount': sum(item.amount for item in summary),
            'medicine_count': len(summary),
        })
    else:
        return redirect('chemist:ch_signin')


def DeleteProduct(request, id):
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        obj = ProductDetails.objects.get(id=id, store_person__cid=username)
        obj.delete()
        messages.success(request, 'Product order removed successfully.')
        return redirect('chemist:ProductListView')
    else:
        return redirect('chemist:ch_signin')


def EditProduct(request, id):
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        model = ProductDetails.objects.get(id=id)
        # form = ProductDetailsForm(request.POST, instance=model)
        if request.POST:
            model.productname=request.POST['productname']
            model.productquantity=request.POST['productquantity']
            model.save()
            messages.success(request, 'Product order updated successfully.')
            return redirect('chemist:ProductListView')
        return render(request, 'store/editproduct.html', {'data': model, 'username': username})
    else:
        return redirect('chemist:ch_signin')

class ProductViewData():
    def __init__(self, supplier_email, name, date, status, payment_status):
        self.supplier_email = supplier_email
        self.name = name
        self.date = date
        self.status = status
        self.payment_status = payment_status

def getStatusInStr(isStatus, isDeny):
    if isStatus == True:
        return "Accepted"
    else:
        if isDeny == True:
            return "Denied"
        return "Pending"

def Dashboard(request):
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        store = ChemistRegister.objects.get(cid=username)

        pdBill = SK_Bills.objects.filter(store_person=store)
        Bcount = 0
        bset = set()
        for i in pdBill:
            bset.add(str(i.Bill_No))

        bset = list(bset)

        model = ProductDetails.objects.filter(store_person=store).count()
        today_stock = ProductDetails.objects.filter(
            store_person=store, date=date.today())
        qty = 0
        today_date = date.today

        acceptedData = ProductDetails.objects.filter(store_person=store).select_related('supplier')
        acceptedData = map(lambda product: ProductViewData(product.supplier.uid if product.supplier else 'Legacy supplier', getattr(product, 'productname'), getattr(product, 'date'), getStatusInStr(getattr(product, 'status'), getattr(product, 'isDeny')), getattr(product, 'payment_status', 'Paid')), acceptedData)

        for i in today_stock:
            qty += i.productquantity
        return render(request, 'store/dashboard.html', {'acceptedData' : acceptedData, 'bset': bset, 'Bcount': len(bset), 'data': model, 'total': qty, 'date': today_date, 'username': username})
    else:
        return redirect('chemist:ch_signin')

def SK_View_Bills(request, ids):
    if CHEMIST_SESSION_KEY not in request.session:
        return redirect('chemist:ch_signin')
    store = ChemistRegister.objects.get(cid=request.session[CHEMIST_SESSION_KEY])
    pdBill = SK_Bills.objects.filter(Bill_No=ids, store_person=store).select_related('supplier')
    tot = 0.0
    date = ""
    sperson = ''
    supplier_email = ''
    payment_status = 'Pending'
    for i in pdBill:
        date = i.date_data
        sperson = i.store_person
        supplier_email = i.supplier.uid if i.supplier else ''
        tot += float(i.pd_tot)
    if pdBill and all(is_payment_paid(i.payment_status) for i in pdBill):
        payment_status = pdBill[0].payment_status
    return render(request, 'store/SK_Order_Bill.html', {'billNo': ids, 'sperson': sperson, 'supplier_email': supplier_email, 'ddate': date, 'tot': tot, 'BillDes': pdBill, 'payment_status': payment_status, 'payment_pending': not is_payment_paid(payment_status)})

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None



def SK_Create_Pdf(request, dt):
    if CHEMIST_SESSION_KEY in request.session:
        username = request.session[CHEMIST_SESSION_KEY]
        store = ChemistRegister.objects.get(cid=username)
        sa=store.chemistaddress
        sc=store.chemistcontactno
        sn=store.chemistmname



        pdBill = SK_Bills.objects.filter(Bill_No=dt, store_person=store).select_related('supplier')
        tot = 0.0
        date = ""
        sperson = ''
        supplier_email = ''
        payment_status = 'Pending'
        for i in pdBill:
            date = i.date_data
            sperson = i.store_person
            supplier_email = i.supplier.uid if i.supplier else ''
            tot += float(i.pd_tot)
        if pdBill and all(is_payment_paid(i.payment_status) for i in pdBill):
            payment_status = pdBill[0].payment_status
        date=date

        Order_Data = {}

        obj_data = SK_Bills.objects.filter(Bill_No=dt, store_person=store)

        prod_price = 0
        prod_qty = 0
        qty = 0
        new = {}
        grand_tot = 0
        for i in obj_data:
            recd_data = {}

            recd_data["prod_price"] = i.pd_tot
            grand_tot += i.pd_tot
            recd_data["prod_qty"] = i.pd_qty
            recd_data['real_price'] = i.pd_price
            new[str(i.pd_nm)] = recd_data

        Order_Data[store] = new

        data = {
            'data': Order_Data,
            'grand_tot': grand_tot,
            'sa': sa,
            'sn': sn,
            'sc': sc,
            'store': store,
            'date': date,
            'SD': store,
            'ADD': sa,
            'CON': sc,
            'NAME': ' '.join(filter(None, [store.chemistfname, store.chemistmname, store.chemistlname])),
            'invoice_no': dt,
            'invoice_date': date,
            'supplier_email': supplier_email,
            'payment_status': payment_status,
            'payment_note': 'Payment completed' if is_payment_paid(payment_status) else 'Payment pending',
        }

        pdf = render_to_pdf('admin/Create_Pdf.html', data)
        return HttpResponse(pdf, content_type='application/pdf')
    # else:
    #     return redirect('LoginView')
