import os

from django.shortcuts import render,redirect,get_object_or_404
from django.http import request,HttpResponseRedirect,HttpResponse,JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.db.models import Q
from email.message import EmailMessage

from .models import UserRegister,cart,UserQuery
from .forms import UserRegisterForm,UserQueryForm
from Chemist_Master.models import StoreDetails,ProductDetails,StockDetails,SK_Bills,ChemistRegister
from med.models import Medicine

from guide.models import guides

import csv
import math
import pandas as pd 
import numpy as np 
from sklearn.linear_model import LinearRegression


import random
#email
import smtplib, ssl


from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa

from django.http import HttpResponse
from django.views.generic import View

import pdfkit
import datetime
import pytz
import time
from datetime import datetime, timezone, date


# from practice.decorator import status
from plotly.offline import plot
from plotly.graph_objs import Scatter

import pdfkit

USER_SESSION_KEY = 'user'

def get_current_supplier(request):
    return UserRegister.objects.get(uid=request.session[USER_SESSION_KEY])


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


def next_month_key():
    today = date.today()
    month = today.month + 1
    year = today.year
    if month == 13:
        month = 1
        year += 1
    return year * 12 + month


def predict_product_demand(monthly_quantity, target_index):
    if not monthly_quantity:
        return 0, 'No history', 'Low'
    sorted_months = sorted(monthly_quantity)
    values = [monthly_quantity[month] for month in sorted_months]
    if len(sorted_months) >= 6:
        model = LinearRegression()
        model.fit(np.array(sorted_months).reshape(-1, 1), np.array(values).reshape(-1, 1))
        predicted = int(round(max(0, model.predict(np.array([[target_index]]))[0][0])))
        method = 'Trend'
    else:
        predicted = int(round(sum(values) / len(values)))
        method = 'Average'

    if len(sorted_months) >= 9:
        confidence = 'Good'
    elif len(sorted_months) >= 4:
        confidence = 'Medium'
    else:
        confidence = 'Low'
    return predicted, method, confidence


def build_stock_ai_insights(supplier, stocks):
    target_index = next_month_key()
    bills = SK_Bills.objects.filter(supplier=supplier)
    insights = {}
    for stock in stocks:
        monthly_quantity = {}
        product_bills = bills.filter(pd_nm__iexact=stock.productName)
        for bill in product_bills:
            bill_date = bill.generated_on.date() if bill.generated_on else bill.date_data
            if not bill_date:
                continue
            month_index = bill_date.year * 12 + bill_date.month
            monthly_quantity[month_index] = monthly_quantity.get(month_index, 0) + int(bill.pd_qty)

        predicted, method, confidence = predict_product_demand(monthly_quantity, target_index)
        suggested_stock = int(math.ceil(predicted * 1.10))
        need_to_add = max(0, suggested_stock - stock.quantity)

        if not monthly_quantity:
            status, status_class = 'No AI history', 'neutral'
        elif stock.quantity < predicted:
            status, status_class = 'Low stock', 'denied'
        elif stock.quantity < suggested_stock:
            status, status_class = 'Reorder soon', 'pending'
        elif suggested_stock and stock.quantity > suggested_stock * 2:
            status, status_class = 'Overstock watch', 'neutral'
        else:
            status, status_class = 'Sufficient', 'accepted'

        insights[stock.id] = {
            'predicted': predicted,
            'suggested_stock': suggested_stock,
            'need_to_add': need_to_add,
            'method': method,
            'confidence': confidence,
            'status': status,
            'status_class': status_class,
            'history_months': len(monthly_quantity),
        }
    return insights

def createGraph(request):
    if USER_SESSION_KEY not in request.session:
        return redirect('user:signin')
    supplier = get_current_supplier(request)
    bills = SK_Bills.objects.filter(supplier=supplier).select_related('store_person')
    bills_store = ChemistRegister.objects.filter(
        id__in=bills.exclude(store_person__isnull=True).values_list('store_person_id', flat=True)
    ).order_by('chemistfname', 'cid')
    bills_products = list(
        bills.exclude(pd_nm='').values_list('pd_nm', flat=True).distinct().order_by('pd_nm')
    )
    month_options = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
    ]
    current_year = date.today().year
    year_options = list(range(current_year, current_year + 4))
    base_context = {
        'store': bills_store,
        'product': bills_products,
        'months': month_options,
        'years': year_options,
    }
    if request.POST:
        s = request.POST.get("store", "")
        p = request.POST.get("product", "")
        requested_month = int(request.POST.get("month", date.today().month))
        requested_year = int(request.POST.get("year", current_year))
        store = get_object_or_404(ChemistRegister, cid=s)
        bills_requested = SK_Bills.objects.filter(
            supplier=supplier,
            store_person=store,
            pd_nm=p
        ).order_by('generated_on', 'date_data', 'id')

        monthly_quantity = {}
        last_bill_date = None
        for bill in bills_requested:
            bill_date = bill.generated_on.date() if bill.generated_on else bill.date_data
            if not bill_date:
                continue
            month_index = bill_date.year * 12 + bill_date.month
            monthly_quantity[month_index] = monthly_quantity.get(month_index, 0) + int(bill.pd_qty)
            if last_bill_date is None or bill_date > last_bill_date:
                last_bill_date = bill_date

        no_date = not monthly_quantity
        plot_div, history_rows = None, []
        prediction = None
        method = ''
        confidence = ''
        confidence_class = 'pending'
        explanation = ''
        current_stock = 0
        suggested_stock = 0
        need_to_add = 0
        target_label = f"{requested_month:02d}-{requested_year}"
        record_count = bills_requested.count()

        if not no_date:
            sorted_months = sorted(monthly_quantity)
            month_labels = []
            month_values = []
            for month_index in sorted_months:
                year = month_index // 12
                month = month_index % 12
                if month == 0:
                    month = 12
                    year -= 1
                label = f"{month:02d}-{year}"
                quantity = monthly_quantity[month_index]
                month_labels.append(label)
                month_values.append(quantity)
                history_rows.append({'period': label, 'quantity': quantity})

            target_index = requested_year * 12 + requested_month
            if len(sorted_months) >= 6:
                model = LinearRegression()
                model.fit(np.array(sorted_months).reshape(-1, 1), np.array(month_values).reshape(-1, 1))
                prediction = int(round(max(0, model.predict(np.array([[target_index]]))[0][0])))
                method = 'Monthly trend regression'
                explanation = 'Enough monthly history was available, so the result follows the demand trend across months.'
            else:
                prediction = int(round(sum(month_values) / len(month_values)))
                method = 'Monthly average fallback'
                explanation = 'History is limited, so the system uses average monthly demand instead of forcing a weak trend.'

            if len(sorted_months) >= 9:
                confidence = 'Good'
                confidence_class = 'accepted'
            elif len(sorted_months) >= 4:
                confidence = 'Medium'
                confidence_class = 'neutral'
            else:
                confidence = 'Low'
                confidence_class = 'pending'

            current_stock_obj = StockDetails.objects.filter(supplier=supplier, productName__iexact=p).first()
            current_stock = current_stock_obj.quantity if current_stock_obj else 0
            suggested_stock = int(math.ceil(prediction * 1.10))
            need_to_add = max(0, suggested_stock - current_stock)

            plot_div = plot([
                Scatter(x=month_labels, y=month_values, mode='lines+markers', name='Historical billed qty', marker_color='#0f766e'),
                Scatter(x=[target_label], y=[prediction], mode='markers', name='Predicted demand', marker_color='#f59e0b', marker_size=12),
            ], output_type='div')

        context = {
            **base_context,
            'year': requested_year,
            'month': requested_month,
            's': s,
            'p': p,
            'selected_store': s,
            'selected_product': p,
            'no_data': no_date,
            'plot_div': plot_div,
            'data': history_rows,
            'prediction': prediction,
            'method': method,
            'confidence': confidence,
            'confidence_class': confidence_class,
            'explanation': explanation,
            'record_count': record_count,
            'month_count': len(monthly_quantity),
            'last_bill_date': last_bill_date,
            'current_stock': current_stock,
            'suggested_stock': suggested_stock,
            'need_to_add': need_to_add,
            'target_label': target_label,
        }
        return render(request, 'admin/newgraph.html', context)
    return render(request, 'admin/newgraph.html', base_context)


# User signin 
def signin(request):
    if request.POST:
        email = request.POST.get('uid', '').strip()
        pass1 = request.POST.get('userpwd', '')
        try:
            valid = UserRegister.objects.get(uid__iexact=email)
            if check_password(pass1, valid.userpwd) or valid.userpwd == pass1:
                request.session[USER_SESSION_KEY] = valid.uid
                if valid.userpwd == pass1:
                    try:
                        valid.userpwd = make_password(pass1)
                        valid.save(update_fields=['userpwd'])
                    except Exception:
                        messages.warning(request, 'Login successful. Password security upgrade will be retried later.')
                return redirect('user:adminDashboard')
            else:
                messages.error(request, 'Invalid email or password. Please check your login details.')
        except UserRegister.DoesNotExist:
            messages.error(request, 'No supplier account found with this email.')
        except Exception:
            messages.error(request, 'Login failed. Please try again.')
    return render(request,'signin1.html')

#User logout
def logout(request):
    if USER_SESSION_KEY in request.session.keys():
        del request.session[USER_SESSION_KEY]
        return redirect('user:index')
    return redirect('user:index')

#User index
def index(request):

    return render(request,'index.html')

#User Index{This indexpage will open after doing signin}
def index1(request):
    if USER_SESSION_KEY in request.session:
        qur=UserQueryForm(request.POST or None)
        if request.method == 'POST' and qur.is_valid():
            qur.save()
            messages.success(request,'Message sent..')
        return render(request,'index1.html',{'qur':qur})
    else:
        return redirect('user:signin')


# User register
def signup(request):
    obj=UserRegisterForm(request.POST if request.method == 'POST' else None)
    
    if obj.is_valid():
        user = obj.save(commit=False)
        user.userpwd = make_password(user.userpwd)
        user.save()
        messages.success(request, 'Supplier account created successfully. Please sign in.')
        return HttpResponseRedirect('/signin/')
    elif request.method == 'POST':
        messages.error(request, 'Please correct the highlighted signup details.')
    return render(request,'signup.html',{'obj':obj})
    

# User can search for medicines using this function
def search(request):
    try:
        serch = request.GET.get('query')
    except:
        serch = None
    if  serch:
        med = guides.objects.all().filter(Q(mname__icontains= serch) | Q(drug__icontains = serch) | Q(symptoms__icontains = serch) | Q(diseases__icontains = serch) )
        data = {
            'med':med
        }
    else:
        data={}
    return render(request,'search1.html',data)

# Forgot Password

def forgot_pass(request):
    email = request.POST.get('email', '').strip()
    if not email:
        return render(request,'email.html')

    if not UserRegister.objects.filter(uid__iexact=email).exists():
        request.session.pop('username', None)
        request.session.pop('otp', None)
        messages.error(request, 'This email is not registered as a supplier. Please use your registered email address.')
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
            message = build_otp_email(email_user, email, otp, 'supplier')
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
    return redirect('user:otpcheck')
        

    return render(request,'email.html')

def otpcheck(request):
    if 'otp' not in request.session:
        messages.error(request, 'OTP session expired. Please request a new OTP.')
        return redirect('user:forgotpass')

    otp = request.session['otp']
    if request.method == 'POST':
        otpobj = request.POST.get('otp', '').strip()
        if otp == otpobj:
            return redirect('user:newpassword')
        messages.error(request, 'Wrong OTP entered. Please check the OTP and try again.')
        return render(request, 'otp.html', {'otp': otpobj})
    return render(request,'otp.html')

def newpassword(request):
    new_pass = request.POST.get('password')
    if request.method == 'POST':
        obj = UserRegister.objects.get(uid = request.session['username'])
        obj.userpwd = make_password(new_pass)
        obj.save()
        return redirect('user:signin')
    return render(request,'forgotpassword.html')
#Add to cart 



def add_to_cart(request):
    if USER_SESSION_KEY in request.session:
        data = request.session[USER_SESSION_KEY]
        ur = UserRegister.objects.get(uid=data)
        context={}
        items = cart.objects.filter(user = ur)
        context['items'] = items
        context['users'] = ur

        if request.method == "POST":
            mid = request.POST["mid"]
            qty = request.POST["qty"]
            # data = request.user.id
            is_exist =  cart.objects.filter(medicine__id = mid,user = ur,status= False)
            if len(is_exist)>0:
                context['msz'] = "Alredy in your cart"
                context['cls'] = "alert alert-warning"
            else:
                medicine = get_object_or_404(guides,id=mid)
                # usr = get_object_or_404(UserRegister,id=request.user.id)
                c = cart(user=ur ,medicine = medicine, quantity=qty)
                c.save()
                context['msz'] = "Added in your cart"
                context['cls'] = "alert alert-success"
              
        return render(request,'cart.html',context)
    else:
        return redirect('user:signin')

def get_cart_data(request):
    if USER_SESSION_KEY in request.session:
        data = request.session[USER_SESSION_KEY]
        ur = UserRegister.objects.get(uid=data)
        items =  cart.objects.filter(user=ur, status=False)
        total,quantity = 0,0
        for i in items:
            total += float(i.medicine.package_price)*i.quantity
            quantity += float(i.quantity)

        res = {
            "Total":total, 
            "quan":quantity
        }
        return JsonResponse(res)
    else:
        return redirect('user:signin')

def change_quan(request):
    if "quantity" in request.GET:
        cid = request.GET["cid"]
        qty = max(0, int(request.GET["quantity"]))
        cart_obj = get_object_or_404(cart,id=cid)
        cart_obj.quantity = qty
        cart_obj.save()
        return HttpResponse(cart_obj.quantity )
    
    if "delete_cart" in request.GET:
        id =request.GET["delete_cart"]
        cart_obj = get_object_or_404(cart,id=id)
        cart_obj.delete()
        return HttpResponseRedirect('/cart/')


def AdminDashboard(request):
    if USER_SESSION_KEY in request.session:
        auser = request.session[USER_SESSION_KEY]
        supplier = get_current_supplier(request)
        bill_history = SK_Bills.objects.filter(
            supplier=supplier
        ).select_related('store_person').order_by('-id')
        total_billed_amount = sum(float(bill.pd_tot) for bill in bill_history)
        bill_payment_pending_count = bill_history.filter(payment_status='Pending').count()

        related_chemist_ids = set(ProductDetails.objects.filter(
            supplier=supplier,
            store_person__isnull=False
        ).values_list('store_person_id', flat=True))
        related_chemist_ids.update(SK_Bills.objects.filter(
            supplier=supplier,
            store_person__isnull=False
        ).values_list('store_person_id', flat=True))
        model = list(ChemistRegister.objects.filter(id__in=related_chemist_ids).order_by('chemistfname', 'cid'))
        for chemist in model:
            chemist.pending_request_count = ProductDetails.objects.filter(
                supplier=supplier,
                store_person=chemist,
                status=False,
                isDeny=False
            ).count()
            chemist.accepted_request_count = ProductDetails.objects.filter(
                supplier=supplier,
                store_person=chemist,
                status=True
            ).count()
            chemist.billed_count = SK_Bills.objects.filter(
                supplier=supplier,
                store_person=chemist
            ).values('Bill_No').distinct().count()
            chemist.payment_pending_count = (
                ProductDetails.objects.filter(
                    supplier=supplier,
                    store_person=chemist,
                    payment_status='Pending'
                ).count() +
                SK_Bills.objects.filter(
                    supplier=supplier,
                    store_person=chemist,
                    payment_status='Pending'
                ).values('Bill_No').distinct().count()
            )
        # predict_graph()

        # print(today.month)
        data = {}
        try:
            q = request.GET.get('search')
        except:
            q = None
        if q:
            product = ChemistRegister.objects.filter(
                Q(cid__icontains=q) | Q(chemistfname__icontains=q) | Q(chemistarea__icontains=q),
                id__in=related_chemist_ids
            )
            product = list(product)
            for chemist in product:
                chemist.pending_request_count = ProductDetails.objects.filter(
                    supplier=supplier,
                    store_person=chemist,
                    status=False,
                    isDeny=False
                ).count()
                chemist.accepted_request_count = ProductDetails.objects.filter(
                    supplier=supplier,
                    store_person=chemist,
                    status=True
                ).count()
                chemist.billed_count = SK_Bills.objects.filter(
                    supplier=supplier,
                    store_person=chemist
                ).values('Bill_No').distinct().count()
                chemist.payment_pending_count = (
                    ProductDetails.objects.filter(
                        supplier=supplier,
                        store_person=chemist,
                        payment_status='Pending'
                    ).count() +
                    SK_Bills.objects.filter(
                        supplier=supplier,
                        store_person=chemist,
                        payment_status='Pending'
                    ).values('Bill_No').distinct().count()
                )
            data = {
                'data': product,
                'StoreDetails': product,
                'auser': auser,
                'bill_history': bill_history,
                'billed_item_count': bill_history.count(),
                'bill_payment_pending_count': bill_payment_pending_count,
                'total_billed_amount': total_billed_amount,
                # 'des': dealer
            }
        else:
            data = {
                'data': model,
                'auser': auser,
                'bill_history': bill_history,
                'billed_item_count': bill_history.count(),
                'bill_payment_pending_count': bill_payment_pending_count,
                'total_billed_amount': total_billed_amount,
            }
        return render(request, 'admin/dashboard.html', data)
    else:
        return redirect('user:signin')
    
def editstock(request, id):
    if USER_SESSION_KEY in request.session:
        supplier = get_current_supplier(request)
        obj1 = get_object_or_404(StockDetails, id=id, supplier=supplier)
        # a = profileform(instance=obj)
        # obj1 = StoreDetails.objects.all()
        if request.POST:
            obj1.productName = request.POST['productName']
            obj1.quantity = request.POST['quantity']
            obj1.price = request.POST['price']
            obj1.save()
            messages.success(request, 'Stock information updated successfully.')
            return redirect('user:viewstock')

        return render(request, 'admin/editstock.html', {'prod': obj1})
    else:
        return redirect('user:signin')

def addstock(request):
    if USER_SESSION_KEY in request.session:
        supplier = get_current_supplier(request)
        form_data = {
            'productName': request.POST.get('productName', '').strip(),
            'quantity': request.POST.get('quantity', '').strip(),
            'price': request.POST.get('price', '').strip(),
        }
        errors = {}

        if request.method == 'POST':
            if not form_data['productName']:
                errors['productName'] = 'Please enter the medicine name.'

            try:
                quantity = int(form_data['quantity'])
                if quantity <= 0:
                    errors['quantity'] = 'Quantity must be greater than zero.'
            except (TypeError, ValueError):
                errors['quantity'] = 'Please enter a valid quantity.'

            try:
                price = float(form_data['price'])
                if price <= 0:
                    errors['price'] = 'Rate must be greater than zero.'
            except (TypeError, ValueError):
                errors['price'] = 'Please enter a valid rate.'

            if not errors:
                stock = StockDetails.objects.filter(
                    supplier=supplier,
                    productName__iexact=form_data['productName']
                ).first()
                if stock:
                    stock.quantity += quantity
                    stock.price = price
                    stock.productName = form_data['productName']
                    stock.save()
                    messages.success(request, f"{stock.productName} stock updated successfully.")
                else:
                    StockDetails.objects.create(
                        supplier=supplier,
                        productName=form_data['productName'],
                        quantity=quantity,
                        price=price
                    )
                    messages.success(request, f"{form_data['productName']} added to stock successfully.")
                return redirect('user:viewstock')

        return render(request, 'admin/addstock.html', {'form_data': form_data, 'errors': errors})
    else:
        return redirect('user:signin')

def viewstore(request, id):

    if USER_SESSION_KEY in request.session:
        supplier = get_current_supplier(request)
        model = ChemistRegister.objects.get(id=id)
        prods = ProductDetails.objects.filter(supplier=supplier, store_person=model, status=False, isDeny=False)
        return render(request, 'admin/storedetails.html', {'data': model, 'prod': prods})
    else:
        return redirect('user:signin')


def editstore(request, id):
    if USER_SESSION_KEY in request.session:
        email = request.session[USER_SESSION_KEY]
        obj1 = ChemistRegister.objects.get(id=id)
        # a = profileform(instance=obj)
        # obj1 = StoreDetails.objects.all()
        if request.POST:
            obj1.chemistfname = request.POST.get('chemistfname', obj1.chemistfname)
            obj1.chemistmname = request.POST.get('chemistmname', obj1.chemistmname)
            obj1.chemistlname = request.POST.get('chemistlname', obj1.chemistlname)
            obj1.cid = request.POST.get('cid', obj1.cid)
            obj1.chemistcontactno = request.POST.get('chemistcontactno', obj1.chemistcontactno)
            obj1.chemistaddress = request.POST.get('chemistaddress', obj1.chemistaddress)
            obj1.chemistarea = request.POST.get('chemistarea', obj1.chemistarea)
            obj1.save()
            messages.success(request, 'Pharmacist profile updated successfully.')
            return redirect('user:adminDashboard')

        return render(request, 'admin/editstore.html', {'shop': obj1})
    else:
        return redirect('user:signin')

def viewstock(request):
    if USER_SESSION_KEY in request.session:
        supplier = get_current_supplier(request)
        model = list(StockDetails.objects.filter(supplier=supplier).order_by('productName'))
        insights = build_stock_ai_insights(supplier, model)
        for stock in model:
            stock.ai = insights.get(stock.id, {})
        return render(request, 'admin/stockdetails.html', {'data': model})
    else:
        return redirect('user:signin')

def accepteddata(request, sk, id):
    supplier = get_current_supplier(request)
    obj = get_object_or_404(ProductDetails, id=id, supplier=supplier)
    obj.status = True
    p_nm = obj.productname
    p_qty = obj.productquantity
    obj.save()

    product_obj = StockDetails.objects.get(supplier=supplier, productName=p_nm)
    if product_obj.quantity < p_qty:
        messages.error(request, f"Only {product_obj.quantity} units of {p_nm} are available.")
        return redirect('user:viewstore', sk)
    product_obj.quantity -= p_qty
    product_obj.save()
    messages.success(request, f"{p_nm} order accepted and stock updated.")
    return redirect('user:viewstore', sk)

def billdata(request, dt):
    supplier = get_current_supplier(request)
    sp = str(dt)
    SD = ChemistRegister.objects.get(cid=str(sp))
    Order_Data = {}

    obj_data = ProductDetails.objects.filter(supplier=supplier, status=True, store_person=SD)
    show = False
    for i in obj_data:
        if not i.Bills_id == "":
            show = True

    qty = 0
    new = {}
    grand_tot = 0
    payment_pending = False
    for i in obj_data:
        recd_data = {}
        qty += 1

        product_qty = int(i.productquantity)

        data = StockDetails.objects.get(supplier=supplier, productName=i.productname)
        rec = float(data.price * product_qty)

        recd_data["prod_price"] = rec
        grand_tot += rec
        recd_data["prod_qty"] = product_qty
        recd_data['real_price'] = data.price
        recd_data['payment_status'] = i.payment_status
        if i.payment_status == 'Pending':
            payment_pending = True
        new[str(data.productName)] = recd_data
    Order_Data[SD] = new
    data={'data': Order_Data, 'grand_tot': grand_tot, 'show': show,'store':SD, 'payment_status': 'Pending' if payment_pending else 'Paid'}
    # pdf = render_to_pdf('admin/billdata.html', data)
    # return HttpResponse(pdf, content_type='application/pdf')
    return render(request, 'admin/billdata.html', {
        'data': Order_Data,
        'grand_tot': grand_tot,
        'show': show,
        'payment_status': data['payment_status'],
    })

def denieddata(request, sk, id):
    supplier = get_current_supplier(request)
    obj = get_object_or_404(ProductDetails, id=id, supplier=supplier)
    obj.isDeny = True
    obj.status = False
    obj.save()
    messages.warning(request, f"{obj.productname} order denied.")
    return redirect('user:viewstore', sk)



def deletestore(request, id):
    if USER_SESSION_KEY in request.session:
        messages.warning(request, 'Chemist account delete is disabled from supplier dashboard to protect order history.')
        return redirect('user:adminDashboard')
    else:
        return redirect('user:signin')




def Confirm_Orders(request):
    if USER_SESSION_KEY not in request.session:
        return redirect('user:signin')
    supplier = get_current_supplier(request)
    obj = ProductDetails.objects.filter(supplier=supplier, status=True)

    data_set = set()
    for i in obj:
        nm = str(i.store_person)
        data_set.add(nm)
    data_set = list(data_set)
    data_set.sort()
    obj1 = data_set
    Order_Data = {}

    for i in obj1:
        recd_data = {}

        data = ChemistRegister.objects.get(cid=str(i))

        obj_data = ProductDetails.objects.filter(
            supplier=supplier, status=True, store_person=data)

        f_total = 0
        prod_qty = 0
        qty = 0
        show = False
        payment_pending = False
        for i in obj_data:
            qty += 1

            prod_qty += int(i.productquantity)
            data = StockDetails.objects.get(supplier=supplier, productName=str(i.productname))
            rec = float(data.price * i.productquantity)
            f_total += rec
            if i.payment_status == 'Pending':
                payment_pending = True
            for i in obj_data:
                if not i.Bills_id == "":
                    show = True

        recd_data["prod_price"] = f_total
        recd_data["prod_qty"] = prod_qty
        recd_data["qty"] = qty
        recd_data['show'] = show
        recd_data['payment_status'] = 'Pending' if payment_pending else 'Paid'
        Order_Data[str(i.store_person)] = recd_data
    return render(request, 'admin/Confirm_orders.html', {'orders': Order_Data})

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def Create_Pdf(request, dt):
    if USER_SESSION_KEY in request.session:
        supplier = get_current_supplier(request)
        tz = pytz.timezone('Asia/Kolkata')
        time_now = datetime.now(timezone.utc).astimezone(tz)
        millis = int(time.mktime(time_now.timetuple()))
        order_id = 'SKBill_Id' + str(supplier.id) + '_' + str(millis)
        Bill_timestamp_no = order_id

        sp = str(dt)
        SD = ChemistRegister.objects.get(cid=str(sp))
        address=SD.chemistaddress
        contact=SD.chemistcontactno
        Name=' '.join(filter(None, [SD.chemistfname, SD.chemistmname, SD.chemistlname]))
        Order_Data = {}

        obj_data = ProductDetails.objects.filter(supplier=supplier, status=True, store_person=SD)

        qty = 0
        new = {}
        grand_tot = 0
        payment_pending = False
        for i in obj_data:
            recd_data = {}
            qty += 1

            product_qty = int(i.productquantity)

            data = StockDetails.objects.get(supplier=supplier, productName=i.productname)
            rec = float(data.price * product_qty)

            recd_data["prod_price"] = rec
            grand_tot += rec
            recd_data["prod_qty"] = product_qty
            recd_data['real_price'] = data.price
            recd_data['payment_status'] = i.payment_status
            if i.payment_status == 'Pending':
                payment_pending = True
            new[str(data.productName)] = recd_data

            skObj = SK_Bills()
            skObj.supplier = supplier
            skObj.store_person = SD
            skObj.Bill_No = str(Bill_timestamp_no)
            skObj.pd_nm = i.productname
            skObj.pd_price = data.price
            skObj.pd_qty = product_qty
            skObj.pd_tot = rec
            skObj.date_data = i.date
            skObj.generated_on = time_now
            skObj.payment_status = i.payment_status
            skObj.save()
            i.delete()
        Order_Data[SD] = new
        payment_status = 'Pending' if payment_pending else 'Paid'
        data = {
            'data': Order_Data,
            'grand_tot': grand_tot,
            'SD': SD,
            'ADD': address,
            'CON': contact,
            'NAME': Name,
            'new': new,
            'invoice_no': Bill_timestamp_no,
            'invoice_date': time_now.strftime('%d-%m-%Y'),
            'supplier_email': request.session.get(USER_SESSION_KEY, ''),
            'payment_status': payment_status,
            'payment_note': 'Payment pending' if payment_pending else 'Payment completed',
        }
        pdf = render_to_pdf('admin/Create_Pdf.html', data)
        return HttpResponse(pdf, content_type='application/pdf')


def Bill_Pdf(request, id):
    if USER_SESSION_KEY not in request.session:
        return redirect('user:signin')

    supplier = get_current_supplier(request)
    selected_bill = get_object_or_404(SK_Bills, id=id, supplier=supplier)
    obj_data = SK_Bills.objects.filter(
        supplier=supplier,
        store_person=selected_bill.store_person,
        Bill_No=selected_bill.Bill_No
    ).select_related('store_person', 'supplier')

    SD = selected_bill.store_person
    if not SD:
        messages.error(request, 'Chemist details are not available for this bill.')
        return redirect('user:adminDashboard')

    new = {}
    grand_tot = 0
    payment_pending = False
    generated_on = selected_bill.generated_on or selected_bill.date_data

    for bill in obj_data:
        new[str(bill.pd_nm)] = {
            'prod_price': bill.pd_tot,
            'prod_qty': bill.pd_qty,
            'real_price': bill.pd_price,
            'payment_status': bill.payment_status,
        }
        grand_tot += bill.pd_tot
        if bill.payment_status == 'Pending':
            payment_pending = True

    data = {
        'data': {SD: new},
        'grand_tot': grand_tot,
        'SD': SD,
        'ADD': SD.chemistaddress,
        'CON': SD.chemistcontactno,
        'NAME': ' '.join(filter(None, [SD.chemistfname, SD.chemistmname, SD.chemistlname])),
        'new': new,
        'invoice_no': selected_bill.Bill_No,
        'invoice_date': generated_on,
        'supplier_email': supplier.uid,
        'payment_status': 'Pending' if payment_pending else 'Paid',
        'payment_note': 'Payment pending' if payment_pending else 'Payment completed',
    }
    pdf = render_to_pdf('admin/Create_Pdf.html', data)
    return HttpResponse(pdf, content_type='application/pdf')
