from django.urls import path
from Chemist_Master.views import paymentData,PayProductOrder,PayBill,SK_Create_Pdf,SK_View_Bills,Dashboard,DeleteProduct,EditProduct,ProductListView,ReceivedStockView,order_medicine,chemist_index,chemist_signup,chemist_signin,Uploaded_Medi,update_med,delete_med,logout,forgot_pass,otpcheck,newpassword,order_medicine

urlpatterns = [
    # signin,signup,indexpage
    path('signin/',chemist_signin,name="ch_signin"),
    path('signup/',chemist_signup,name="ch_signup"),
    path('',chemist_index,name="ch_index"),
    #Chemist interactions with medicines
    path('Uploaded_Medi/',Uploaded_Medi,name='Uploaded_Medi'),
    path('update_med/<int:id>',update_med,name='update_med'),
    path('delete_med/<int:id>',delete_med,name='delete_med'),
    path('order-medicine/',order_medicine,name='order-medicine'),
    path('productlist/', ProductListView, name='ProductListView'),
    path('received-stock/', ReceivedStockView, name='ReceivedStockView'),
    path('dashboard/', Dashboard, name='Dashboard'),
    path('paymentpage/', paymentData, name='paymentData'),
    path('pay-order/<int:id>/', PayProductOrder, name='pay_product_order'),
    path('pay-bill/<str:bill_no>/', PayBill, name='pay_bill'),
    #path('paymentSuccess/',paymentSuccess,name="paymentSuccess"),

    path('deleteproduct/<int:id>', DeleteProduct, name='deleteproduct'),
    path('editproduct/<int:id>', EditProduct, name='editproduct'),
    
    #Logout
    path('logout/',logout,name='logout'),
    
    # Forgot Password
    path('forgot_pass/',forgot_pass,name="forgotpass"),
    path('otpcheck/',otpcheck,name="otpcheck"),
    path('newpassword/',newpassword,name="newpassword"),
    path('View_Bills/<str:ids>', SK_View_Bills, name='SK_View_Bills'),
    path('SK_create_pdf/<str:dt>',SK_Create_Pdf, name='sk_create_pdf'),

    
]
