from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
  path('signup',views.user_registration,name='signup'),
  path('signin',views.login_view,name='signin'),
  path('logout',views.logout_view,name='logout'),
  path('get_deposit_address',views.get_deposit_address, name='get_deposit_address'),
  path('process_deposit',views.process_deposit,name='process_deposit'),
  path('password_reset',views.password_reset_view, name='password_reset'),
  path('verify_email/', views.verify_email_view, name='verify_email'),
  path('password_reset/<str:token>/', views.password_confirmation_view, name='password_confirmation_view'),
  path('reset_password/<str:token>/', views.reset_view, name='reset_view'),
  path('send-verification-code/',views.send_verification_code, name='send_verification_code'),
  path('verify-code/',views.verify_code, name='verify_code'), 
  path('request_withdrawal_code',views.request_withdrawal_code,name='request_withdrawal_code'),
  path('verify_withdrawal_code',views.verify_withdrawal_code,name='verify_withdrawal_code'),
  path('request-transfer-code/',views.request_transfer_code, name='request_transfer_code'), 
  path('verify-transfer-code/',views.verify_transfer_code, name='verify_transfer_code'), 
  path('account/settings/', views.account_settings, name='account_settings'), 
  path('toggle-daily-savings/', views.toggle_daily_savings, name='toggle_daily_savings'),
  path('withdraw_daily_savings',views.withdraw_view,name='withdraw_daily_savings'),
  path('save_monthly_savings/',views.save_monthly_savings,name='save_monthly_savings'),
  path('save_yearly_savings',views.save_yearly_savings,name='save_yearly_savings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
