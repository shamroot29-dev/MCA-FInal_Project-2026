from django.urls import path
from  User_Master import views


urlpatterns = [

    #User Signin,Signup,Logout,IndexpagenIndexpage1
    path('signin/',views.signin,name="signin"),
    path('signup/',views.signup,name="signup"),
    path('logout/',views.logout,name='logout'),
    path('',views.index,name="index"),
    path('Userindex/',views.index1,name="Userindex"),

    #User search function
    path('search/',views.search, name = "search"),
    
    #User Forgot Password
    path('forgot_pass/',views.forgot_pass,name="forgotpass"),
    path('otpcheck/',views.otpcheck,name="otpcheck"),
    path('newpassword/',views.newpassword,name="newpassword"),
    
    #User Add to Cart
    path('cart/',views.add_to_cart, name="cart"),
    path('getcartData/',views.get_cart_data, name = "cartData"),
    path('changedata/',views.change_quan,name="changeData"),
    
    # -------------changes------
    path('adminDashboard/', views.AdminDashboard, name='adminDashboard'),
    path('storeview/<int:id>', views.viewstore, name='viewstore'),
    path('viewstock/', views.viewstock, name='viewstock'),
    path('addstock/', views.addstock, name='addstock'),
    path('editstock/<int:id>', views.editstock, name='editstock'),


    path('storeedit/<int:id>', views.editstore, name='editstore'),
    path('storedelete/<int:id>', views.deletestore, name='deletestore'),
    path('Confirm_Orders/', views.Confirm_Orders, name="confirm_order"),

    path('accept_data/<int:sk>/<int:id>/', views.accepteddata, name='accept_data'),
    path('denied_data/<int:sk>/<int:id>/', views.denieddata, name='denied_data'),    
    path('billdata/<str:dt>', views.billdata, name='billdata'),
    path('create_pdf/<str:dt>', views.Create_Pdf, name='create_pdf'),
    path('bill_pdf/<int:id>/', views.Bill_Pdf, name='bill_pdf'),
    path('createGraph/', views.createGraph, name="createGraph"),

]
