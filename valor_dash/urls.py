from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home_dash'),
    path('register',views.register,name='register'),
    path('login',views.login,name='login'),
    path('accounts',views.Accounts,name='accounts'),
    path('Transactions',views.Transactions,name='Transactions'),
    path('Savings',views.Savings,name='Savings'),
    path('reset_password',views.reset_password,name='reset_password'),
    path('password_reset',views.password_reset,name='password_reset'),
]
