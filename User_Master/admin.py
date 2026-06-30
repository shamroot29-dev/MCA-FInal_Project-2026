from django.contrib import admin

# Register your models here.

from .models import UserRegister,UserQuery

class UserRegisterAdmin(admin.ModelAdmin):
        list_display=['uid','userfname','usermname','userlname','useraddress','usercity','userarea','userpincode','usercontactno']


admin.site.register(UserRegister,UserRegisterAdmin)
admin.site.register(UserQuery)

admin.site.site_header = 'pharmacy administration'
admin.site.site_title = 'Admin Panel'
admin.site.index_title = 'Pharmacy Admin Panel'
