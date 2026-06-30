from django.contrib import admin
from .models import guides

class guideadmin(admin.ModelAdmin):
    list_display=['mname','side_effect','caution','unit','drug']
admin.site.register(guides,guideadmin)