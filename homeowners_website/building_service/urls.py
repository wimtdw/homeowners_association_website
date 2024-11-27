from django.urls import path
from . import views

app_name = 'building_service'

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/profile/add_account/', views.add_account, name='add_account'),
    path('accounts/profile/add_readings/<str:account_number>/', views.add_readings, name='add_readings'),
    path('accounts/profile/get_bill/<str:account_number>/', views.get_bill, name='get_bill'),
    path('accounts/profile/readings_history/<str:account_number>/', views.readings_history, name='readings_history')
]