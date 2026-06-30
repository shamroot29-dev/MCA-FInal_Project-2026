from django.urls import path,include
from .views import CSV,View


urlpatterns = [
        path('view/<int:pk>/', View,name='vieww'),
        path('csv/',CSV,name='csv'),
    ]

