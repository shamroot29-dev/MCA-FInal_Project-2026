
from django.urls import path
from med import views
from .views import Search
urlpatterns = [
  
    path('add/', views.medi,name='add'),
    path('show/',views.show1,name='show'),
    path("search/<str:para>/",views.show, name="profilesearch"),
    path("search/", Search.as_view(), name="searchpage"),
    path('update/<int:id>', views.update),  
    path('delete/<int:id>', views.destroy), 
]