from django.db import models
from guide.models import guides

# User Details
class UserRegister(models.Model):
    uid=models.EmailField(max_length=50,verbose_name='Email',unique="True")
    userpwd=models.CharField(max_length=128,verbose_name='Password')
    userfname=models.CharField(max_length=20,default='',verbose_name='First_Name')
    usermname=models.CharField(max_length=20,default='',verbose_name='Middle_Name')
    userlname=models.CharField(max_length=20,default='',verbose_name='Last_Name')
    useraddress=models.CharField(max_length=20,default='',verbose_name='Address')
    usercity=models.CharField(max_length=30,default='',verbose_name='City')
    userarea=models.CharField(max_length=20,default='',verbose_name='Area')
    userpincode=models.IntegerField(default='',verbose_name='Pincode')
    usercontactno=models.IntegerField(default='',verbose_name='Contact_No')
    forgot_pass = models.CharField('Write your password hint',max_length=100,default='')

    def __str__(self):
        return self.uid

# Cart Models
class cart(models.Model):
    user = models.ForeignKey(UserRegister,on_delete=models.CASCADE)
    medicine = models.ForeignKey(guides,on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.BooleanField(default=False)
    added_on =models.DateTimeField(auto_now_add=True,null=True)
    update_on = models.DateTimeField(auto_now=True,null=True)

    def __str__(self):
        return self.medicine.mname

class UserQuery(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=200,default='')
    subject= models.CharField(default='',max_length=100)
    message = models.CharField(default='',max_length=500)

    def __str__(self):
        return self.name
