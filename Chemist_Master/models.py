from django.db import models


# Chemist Details
class ChemistRegister(models.Model):
    cid=models.EmailField(max_length=50,verbose_name='Email')
    chemistpwd=models.CharField(max_length=128,verbose_name='Password')
    chemistfname=models.CharField(max_length=20,default='',verbose_name='First_Name')
    chemistmname=models.CharField(max_length=20,default='',verbose_name='Middle_Name')
    chemistlname=models.CharField(max_length=20,default='',verbose_name='Last_Name')
    chemistaddress=models.CharField(max_length=20,default='',verbose_name='Address')
    chemistcity=models.CharField(max_length=20,default='',verbose_name='City')
    chemistarea=models.CharField(max_length=20,default='',verbose_name='Area')
    chemistpincode=models.IntegerField(default='',verbose_name='Pincode')
    chemistcontactno=models.IntegerField(default='',verbose_name='Contact_No')
    chemistphoto = models.FileField(upload_to = 'upload',verbose_name='store certificate',null=True,blank=True)
    forgot_pass = models.CharField('Write your password hint',max_length=100,default='')
    def __str__(self):
        return self.cid


## ------changes--------##
class StoreDetails(models.Model):
    StoreName = models.CharField(max_length = 50,blank = True)
    PersonName = models.CharField(max_length = 50,blank = True)
    Contact = models.IntegerField(blank = True)
    email = models.EmailField(blank = True, default="", max_length=150)
    password = models.CharField(max_length = 50)
    add1 = models.TextField(default="")

    def __str__(self):
        return self.StoreName


class StockDetails(models.Model):
    supplier = models.ForeignKey('User_Master.UserRegister', on_delete=models.CASCADE, null=True, blank=True)
    productName = models.CharField(max_length = 50,blank = True)
    quantity = models.IntegerField()
    price = models.FloatField()

    @property
    def net_price(self):
        return self.quantity * self.price

    def __str__(self):
        return self.productName

class ProductDetails(models.Model):
    supplier = models.ForeignKey('User_Master.UserRegister', on_delete=models.CASCADE, null=True, blank=True)
    store_person = models.ForeignKey('ChemistRegister',on_delete=models.CASCADE, null=True)
    productname = models.CharField(max_length = 50,default="")
    productquantity = models.IntegerField()
    date = models.DateField(auto_now=False,blank=True,null=True)
    status = models.BooleanField(default=False)
    isDeny = models.BooleanField(default=False)
    Bills_id = models.CharField(max_length = 200,default="",null=True,blank=True)
    payment_status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return self.productname


class SK_Bills(models.Model):
    supplier = models.ForeignKey('User_Master.UserRegister', on_delete=models.CASCADE, null=True, blank=True)
    store_person = models.ForeignKey('ChemistRegister',on_delete=models.CASCADE, null=True)
    Bill_No = models.CharField(max_length = 200,default="")
    pd_nm = models.CharField(max_length = 200,default="")
    pd_price = models.FloatField(default=0.0)
    pd_qty = models.IntegerField(default=0)
    pd_tot = models.FloatField(default=0.0)
    date_data = models.DateField(auto_now=False,blank=True,null=True)
    generated_on = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='Paid')
    
    def __str__(self):
        return self.Bill_No
