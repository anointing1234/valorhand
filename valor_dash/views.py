from django.shortcuts import render
from requests.exceptions import ConnectionError, Timeout, RequestException
from accounts.views import RegistrationForm,AccountAuthenticationForm,Transaction,PasswordResetForm,AccountSettingsForm 
from accounts.models import EmailVerification,Deposit,SavingsPercentage,UserSavings

import requests
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def home(request): 
    
    
    account =  request.user  # Assuming each user has an associated Account instance

    # Check if all fields in Account are filled
    all_fields_filled = (
        account.username and
        account.email and
        account.phone and
        account.country
    )
    
    if request.user.is_authenticated:
        # Fetch transactions made by the logged-in user, filtering out incomplete transactions
        recent_transactions = Transaction.objects.filter(
            user=request.user,
            description__isnull=False,
            category__isnull=False,
            amount__isnull=False,
           ).order_by('-date')
    else:
        recent_transactions = []
        
    Main_balance = request.user.balance.main_balance
    formatted_Main_balance = "{:,.2f}".format(Main_balance)

    # Assuming Dollar_balance should also be derived from niara_balance (convert it accordingly if needed)
    total_savings = request.user.balance.total_savings  # or perform conversion here if needed
    formatted_total_savings = "{:,.2f}".format(total_savings)
    

    user = request.user  # Assuming you are using Django's authentication
      # Check if the email exists in the EmailVerification model
    has_deposit = Deposit.objects.filter(user=user).exists()
    is_saved = UserSavings.objects.filter(user=request.user).exists()

# Check if the user has any deposits
  
    try:
        email_verification = EmailVerification.objects.get(email=user.email)
        is_verified = email_verification.is_verified
    except EmailVerification.DoesNotExist:
        is_verified = False  # Email is not registered for verification

   
   
    return render(request, 'dashboard/index.html', {
        'formatted_Main_balance':  formatted_Main_balance,
        'formatted_total_savings':  formatted_total_savings,
        'recent_transactions': recent_transactions,
        'is_verified': is_verified,
        'has_deposit': has_deposit,
        'all_fields_filled': all_fields_filled,
        'is_saved': is_saved,
    })






def login(request):
    form = AccountAuthenticationForm()
    context = {
        'form': form,
    }
    return render(request,'registeration/login.html',context)


def register(request): 
    form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request,'registeration/signup.html',context)

def Accounts(request):
    form = AccountSettingsForm() 
    
    Main_balance = request.user.balance.main_balance
    # Format niara_balance to include commas and two decimal places
    formatted_Main_balance = "{:,.2f}".format(Main_balance)

    # Assuming Dollar_balance should also be derived from niara_balance (convert it accordingly if needed)
    total_savings = request.user.balance.total_savings  # or perform conversion here if needed
    formatted_total_savings = "{:,.2f}".format(total_savings)
    
    user = request.user
    
    try:
        email_verification = EmailVerification.objects.get(email=user.email)
        is_verified = email_verification.is_verified
    except EmailVerification.DoesNotExist:
        is_verified = False  # Email is not registered for verification

    
    
    return render(request,'dashboard/Accounts.html',{
        'formatted_Main_balance': formatted_Main_balance,
        'formatted_total_savings': formatted_total_savings,
        'is_verified': is_verified,
        'form':form
    })




def Transactions(request):
    
    if request.user.is_authenticated:
        
        recent_transactions = Transaction.objects.filter(
            user=request.user,
            category__in=['Withdrawal', 'Deposit', 'Transfer']  # Filter for multiple categories
        ).order_by('-date')[:10]  # Get the last 10 transactions

    Main_balance = request.user.balance.main_balance
    # Format niara_balance to include commas and two decimal places
    formatted_Main_balance = "{:,.2f}".format(Main_balance)
    
    user = request.user
    
    try:
        email_verification = EmailVerification.objects.get(email=user.email)
        is_verified = email_verification.is_verified
    except EmailVerification.DoesNotExist:
        is_verified = False  # Email is not registered for verification

    context = {
            'recent_transactions': recent_transactions,
            'formatted_Main_balance': formatted_Main_balance,
            'is_verified': is_verified,
    }
   
    
    return render(request,'dashboard/Trasactions.html',context)


def Savings(request):
    Main_balance = request.user.balance.main_balance
    # Format niara_balance to include commas and two decimal places
    formatted_Main_balance = "{:,.2f}".format(Main_balance)

    # Assuming Dollar_balance should also be derived from niara_balance (convert it accordingly if needed)
    total_savings = request.user.balance.total_savings  # or perform conversion here if needed
    formatted_total_savings = "{:,.2f}".format(total_savings)
    
    
    daily_savings = request.user.balance.daily_savings  # or perform conversion here if needed
    formatted_daily_savings = "{:,.2f}".format(daily_savings)
    
    monthly_savings = request.user.balance.monthly_savings  # or perform conversion here if needed
    formatted_monthly_savings = "{:,.2f}".format(monthly_savings)
    
    yearly_savings = request.user.balance.yearly_savings  # or perform conversion here if needed
    formatted_yearly_savings = "{:,.2f}".format(yearly_savings)
    
    
    user = request.user
    
    try:
        email_verification = EmailVerification.objects.get(email=user.email)
        is_verified = email_verification.is_verified
    except EmailVerification.DoesNotExist:
        is_verified = False  # Email is not registered for verification
    
    try:
        savings_percentage = SavingsPercentage.objects.get()
        daily_savings_percentage = "{:.0f}".format(savings_percentage.daily_savings_percentage)
        monthly_savings_percentage = "{:.0f}".format(savings_percentage.monthly_savings_percentage)
        yearly_savings_percentage = "{:.0f}".format(savings_percentage.yearly_savings_percentage)
    except SavingsPercentage.DoesNotExist:
        daily_savings_percentage = 0
        monthly_savings_percentage = 0
        yearly_savings_percentage = 0 
    
    user_savings = UserSavings.objects.filter(user=request.user).first()
    is_daily_savings_active = user_savings.is_daily_savings_active if user_savings else False
    
    savings_transactions = Transaction.objects.filter(user=user, category='Savings').order_by('-date')[:5]  # Fetch the 10 most recent savings transactions    
    
    return render(request,'dashboard/Savings.html', {
        'formatted_Main_balance': formatted_Main_balance,
        'formatted_total_savings': formatted_total_savings,
        'formatted_daily_savings': formatted_daily_savings,
        'formatted_monthly_savings': formatted_monthly_savings,
        'formatted_yearly_savings': formatted_yearly_savings,
        'daily_savings_percentage': daily_savings_percentage,
        'monthly_savings_percentage': monthly_savings_percentage,
        'yearly_savings_percentage': yearly_savings_percentage,
        'is_verified': is_verified,
        'is_daily_savings_active': is_daily_savings_active,
        'savings_transactions': savings_transactions,
    })
  

    

def reset_password(request):
    form = PasswordResetForm()
    context = {
        'form': form,
    }
    return render(request,'registeration/reset_password.html',context)   

def password_reset(request):
    return render(request,'registeration/password_update.html')

