from django.contrib import admin
from django.urls import path, include
from .views import SignUpView
from . import views

app_name = 'users'

urlpatterns = [
    path('', SignUpView.as_view(), name='registration')
]