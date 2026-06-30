from django.contrib import admin
from .models import Medicine

class medAdmin(admin.ModelAdmin):
    list_display=['m_name','quantity','amount','formulation']
#admin.site.register(Medicine,medAdmin)

