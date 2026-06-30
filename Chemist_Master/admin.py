from django.contrib import admin
from Chemist_Master.models import SK_Bills,ChemistRegister,StockDetails,ProductDetails,StoreDetails

class ChemistRegisterAdmin(admin.ModelAdmin):
    list_display=['cid','chemistfname','chemistmname','chemistlname','chemistaddress','chemistcity','chemistarea','chemistpincode','chemistcontactno','chemistphoto']

admin.site.register(ChemistRegister,ChemistRegisterAdmin)
admin.site.register(StockDetails)
admin.site.register(ProductDetails)
admin.site.register(SK_Bills)