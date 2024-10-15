from django.shortcuts import render
from .models import Account
from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils.html import strip_tags
from django.contrib.auth import login,authenticate,logout as auth_logout
from accounts.forms import RegistrationForm,AccountAuthenticationForm,PasswordResetForm,AccountSettingsForm
from django.contrib import messages
from django.urls import reverse
import random
import string
import shutil
import os
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from requests.exceptions import ConnectionError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import DepositAddress,Transaction,Balance,Deposit,EmailVerification,VerificationCode,Withdrawal,Transfer,UserSavings,SavingsPercentage
from django.contrib.auth.decorators import login_required
import json
from django.core.mail import send_mail
import requests 
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import Signer, BadSignature
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from .config import PASSWORD_RESET_URL_TEMPLATE
from requests.exceptions import ConnectionError
import requests 





PASSWORD_RESET_TIMEOUT = 20

def password_similarity_check(password):
    # Define a list of common password patterns
    common_patterns = ["password", "qwerty", "123456", "abc123"]

    # Check if the password contains any common patterns
    for pattern in common_patterns:
        if pattern in password.lower():
            raise ValidationError("Password is too similar to a common pattern.")

def user_registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Check if email or username already exists
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            if Account.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email is already registered.'})
            elif Account.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username is already taken.'})
            
            # Check if the passwords match
            raw_password = form.cleaned_data.get('password1')
            confirm_password = form.cleaned_data.get('password2')
            if raw_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match.'})

            # Check password strength and similarity
            try:
                validate_password(raw_password)
                password_similarity_check(raw_password)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': e.message})

            # Create user and authenticate
            user = form.save(commit=False)  # Don't save to database yet
            user.set_password(raw_password)  # Hash the password
            user.save()  # Save user with hashed password

            # Authenticate and login the user
            account = authenticate(email=user.email, password=raw_password)
            if account is not None:
                login(request, account)
                messages.success(request, 'Registration successful. You are now logged in.')
                return JsonResponse({'success': True, 'message': 'Registration successful! You are now logged in.', 'redirect_url': '/login'})
            else:
                messages.error(request, 'Registration successful, but authentication failed. Please try logging in.')
                return JsonResponse({'success': False, 'message': 'Registration successful, but authentication failed. Please try logging in.'})

        else:
            # If form is not valid, send form errors as JSON
            errors = form.errors.as_json()  # Get form errors as JSON
            return JsonResponse({'success': False, 'errors': errors})
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'registeration/signup.html', context)


def login_view(request):
    if request.method == 'POST':
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Get the user object based on the email
            try:
                user = Account.objects.get(email=email)  # Fetch user from the Account model
            except Account.DoesNotExist:
                # Respond with error if user does not exist
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid email or password.'
                })

            # Check if the password is correct using check_password
            if user.check_password(password):  # Verifies the hashed password
                login(request, user)
                # Respond with success message
                return JsonResponse({
                    'success': True,
                })
            else:
                # If password check fails
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid email or password.'
                })
        else:
            # If the form is invalid
            return JsonResponse({
                'success': False,
                'errors': form.errors.as_json()
            })

    else:
        form = AccountAuthenticationForm()

    return render(request, 'registeration/login.html', {'form': form})




@login_required
def get_deposit_address(request):
    if request.method == 'GET':
        # You can adjust how 'balance_type' or any relevant parameter is used in your business logic
        balance_type = request.GET.get('balance_type')  # Assuming balance_type helps differentiate other logic

        try:
            # Fetch the deposit address for the dynamically chosen wallet type by the admin
            deposit_address = DepositAddress.objects.first()  # Fetch the first DepositAddress entry

            if deposit_address:  # If there's a deposit address available
                data = {
                    'wallet_address': deposit_address.usdt_wallet_address,
                    'wallet_type': deposit_address.wallet_type,  # Add the wallet type for information
                }
                return JsonResponse({'success': True, 'data': data})
            else:
                return JsonResponse({'success': False, 'message': 'No deposit address found in the system.'})

        except DepositAddress.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Deposit address not found.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})



@login_required
def process_deposit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = Decimal(data.get('amount'))  # Ensure the amount is a Decimal for accuracy

            user = request.user

            # Fetch the user's balance
            balance = Balance.objects.get(user=user)

            description = f"Deposit of ${amount} to Main Balance"

            # Log the deposit in the Deposit model
            Deposit.objects.create(
                user=user,
                amount=amount,
                status='Pending',
                balance_type='main_balance'  # Save 'main_balance' as the balance type
            )

            # Log the transaction in the Transaction model
            Transaction.objects.create(
                user=user,
                description=description,
                category='Deposit',
                amount=amount,
                status='Pending'
            )

            # Return a success response
            return JsonResponse({'success': True, 'message': 'Deposit successfully processed and transaction logged.'})

        except Balance.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User balance not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

    # Return error if the request method is not POST
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def confirm_deposit(request):
    deposit_id = request.GET.get('deposit_id')  # Get the deposit ID from the query parameter
    deposit = get_object_or_404(Deposit, id=deposit_id)

    if deposit.status == 'Pending':
        # Retrieve user's balance
        balance = Balance.objects.get(user=deposit.user)

        # Initialize daily savings amount
        daily_savings_amount = Decimal('0.00')

        # Check if daily savings are active for the user
        user_savings = UserSavings.objects.filter(user=deposit.user).first()
        
        # Fetch the daily savings percentage
        savings_percentage = SavingsPercentage.objects.first()  # Assuming only one instance exists

        if user_savings and user_savings.is_daily_savings_active:
            # Calculate the daily savings deduction
            if savings_percentage:
                daily_savings_percentage = savings_percentage.daily_savings_percentage
                daily_savings_amount = (deposit.amount * daily_savings_percentage) / Decimal('100')
                
                print(f"Daily Savings Percentage: {daily_savings_percentage}, Daily Savings Amount: {daily_savings_amount}")

                # Update the UserSavings model
                user_savings.amount += daily_savings_amount
                user_savings.profit_percentage = daily_savings_percentage 
                user_savings.save()  # Save the updated savings

                # Update the daily savings in the Balance model
                balance.daily_savings += daily_savings_amount
                balance.total_savings += daily_savings_amount  # Optionally update total savings as well

        # Update user's balance based on deposit type
        if deposit.balance_type == 'main_balance':
            balance.main_balance += (deposit.amount - daily_savings_amount)  # Deduct daily savings from deposit before updating balance
        balance.save()  # Save the updated balance

        # Update deposit status
        deposit.status = 'Completed'

        # Retrieve the existing transaction for the deposit
        transaction = Transaction.objects.filter(user=deposit.user, amount=deposit.amount, category='Deposit', status='Pending').first()

        if transaction:
            # Update the existing transaction status
            transaction.status = 'Completed'
            transaction.description = f"Deposit confirmed: {deposit.amount} {deposit.balance_type}"
            transaction.save()  # Save changes to the transaction
        else:
            messages.warning(request, "No pending transaction found to update.")
        
        # Create a new transaction for the savings
        if daily_savings_amount > 0:
            savings_transaction = Transaction(
                user=deposit.user,
                amount=daily_savings_amount,
                category='Savings',
                status='Completed',
                description=f"Daily savings added: {daily_savings_amount} for deposit ID: {deposit.id}"
            )
            savings_transaction.save()     
            

        deposit.save()  # Save the deposit status change
        messages.success(request, f"Deposit of {deposit.amount} confirmed successfully.")
    else:
        messages.warning(request, f"Deposit is already {deposit.status}.")

    return redirect('admin:accounts_deposit_changelist')


# Decline deposit view
def decline_deposit(request):
    deposit_id = request.GET.get('deposit_id')  # Get the deposit ID from the query parameter
    deposit = get_object_or_404(Deposit, id=deposit_id)

    if deposit.status == 'Pending':
        # Update deposit status
        deposit.status = 'Declined'

        # Retrieve the existing transaction for the deposit
        transaction = Transaction.objects.filter(user=deposit.user, amount=deposit.amount, category='Deposit', status='Pending').first()

        if transaction:
            # Update the existing transaction status
            transaction.status = 'Failed'
            transaction.description = f"Deposit declined: {deposit.amount} {deposit.balance_type}"
            transaction.save()  # Save changes to the transaction
        else:
            messages.warning(request, "No pending transaction found to update.")

        deposit.save()  # Save the deposit status change
        messages.success(request, f"Deposit has been declined.")
    else:
        messages.warning(request, f"Deposit is already {deposit.status}.")

    return redirect('admin:accounts_deposit_changelist')







# Confirm withdrawal view
def confirm_withdrawal(request):
    withdrawal_id = request.GET.get('withdrawal_id')  # Get the withdrawal ID from the query parameter
    withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)

    if withdrawal.status == 'Pending':
        withdrawal.status = 'Completed'

        # Retrieve the existing transaction for the withdrawal
        transaction = Transaction.objects.filter(
            user=withdrawal.user,
            amount=withdrawal.amount,
            category='Withdrawal',  # Ensure category matches the withdrawal
            status='Pending'
        ).first()

        if transaction:
            # Update the existing transaction status
            transaction.status = 'Completed'
            transaction.description = f"Withdrawal confirmed: {withdrawal.amount} USDT"
            transaction.save()  # Save changes to the transaction
        else:
            messages.warning(request, "No pending transaction found to update.")

        withdrawal.save()  # Save the withdrawal status change
        messages.success(request, f"Withdrawal of {withdrawal.amount} confirmed successfully.")
    else:
        messages.warning(request, f"Withdrawal is already {withdrawal.status}.")

    return redirect('admin:accounts_withdrawal_changelist')


# Decline withdrawal view
def decline_withdrawal(request):
    withdrawal_id = request.GET.get('withdrawal_id')  # Get the withdrawal ID from the query parameter
    withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)  # Use Withdrawal model

    if withdrawal.status == 'Pending':
        # Update withdrawal status
        withdrawal.status = 'Declined'

        # Retrieve the existing transaction for the withdrawal
        transaction = Transaction.objects.filter(
            user=withdrawal.user,
            amount=withdrawal.amount,
            category='Withdrawal',  # Ensure category matches the withdrawal
            status='Pending'
        ).first()

        if transaction:
            # Update the existing transaction status
            transaction.status = 'Failed'
            transaction.description = f"Withdrawal declined: {withdrawal.amount} USDT"
            transaction.save()  # Save changes to the transaction
        else:
            messages.warning(request, "No pending transaction found to update.")

        withdrawal.save()  # Save the withdrawal status change
        messages.success(request, "Withdrawal has been declined.")
    else:
        messages.warning(request, f"Withdrawal is already {withdrawal.status}.")

    return redirect('admin:accounts_withdrawal_changelist')








# user logout views-----------------------
def logout_view(request):
    auth_logout(request)
    form = AccountAuthenticationForm()
    context = {
        'form': form,
    }
    return render(request,'registeration/login.html',context)

    

def password_reset_view(request):
    if request.method == 'POST':
        try:
            # Check for internet connection by making a request to a reliable URL
            requests.get("http://www.google.com", timeout=5)
        except requests.ConnectionError:
            return JsonResponse({'status': 'error', 'message': 'No internet connection'}, status=500)

        data = json.loads(request.body)
        email = data.get('email')
        user = Account.objects.filter(email=email).first()

        if user:
            # Generate a token and an expiration timestamp
            signer = Signer()
            token = signer.sign(user.id)  # You can include more data in the token if needed
            expiration_time = timezone.now() + timezone.timedelta(minutes=PASSWORD_RESET_TIMEOUT)

            # Create the password reset link
            reset_link = PASSWORD_RESET_URL_TEMPLATE

            try:
                send_mail(
                    'Password Reset Request',
                    f'Here is the link to reset your password: {reset_link}\nThis link will expire in {PASSWORD_RESET_TIMEOUT} minutes.When it expires you will be redirected to login page',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=400)

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    form = PasswordResetForm()
    return render(request,'registeration/login.html', {'form': form})



# View to display password confirmation page (via reset link)
def password_confirmation_view(request, token):
    signer = Signer()
    try:
        # Verify the token
        user_id = signer.unsign(token)
        user = Account.objects.get(id=user_id)
    except (BadSignature, Account.DoesNotExist):
        messages.error(request, 'Invalid or expired token.')
        return redirect('login')  # Redirect to login if token is invalid

    return render(request, 'registeration/password_update.html', {'token': token})


def reset_view(request, token):
    if request.method == 'POST':
        signer = Signer()
        try:
            # Verify the token and get user
            user_id = signer.unsign(token)
            user = Account.objects.get(id=user_id)

            # Print the user's email and hashed password for testing
            print(f"User email: {user.email}")  # Print email
            print(f"Hashed old password (in DB): {user.password}")  # Print hashed password from DB

        except (BadSignature, Account.DoesNotExist):
            return JsonResponse({'message': 'Invalid or expired token.'}, status=400)

        # Get the new password and confirm password from the POST data
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Print out the new password the user is attempting to set for testing purposes
        print(f"New password entered: {new_password}")  # Testing: Print the new password

        if new_password != confirm_password:
            return JsonResponse({'message': 'Passwords do not match.'}, status=400)

        # Update password securely (hashed)
        user.password = make_password(new_password)
        user.save()

        return JsonResponse({'message': 'Your password has been updated successfully.'})

    return render(request, 'registeration/password_update.html', {'token': token})


def verify_email_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Parse the JSON request body
        email = data.get('email')

        # Check if the email exists in the custom Account model
        email_exists = Account.objects.filter(email=email).exists()

        # Return the response based on whether the email exists
        if email_exists:
            return JsonResponse({'exists': True, 'message': 'Email is registered.'})
        else:
            return JsonResponse({'exists': False, 'message': 'This email is not registered.'})

    return JsonResponse({'error': 'Invalid request'}, status=400)





def send_verification_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Get the JSON data
        email = data.get('email')

        # Check if the email exists in the custom user model
        if not Account.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email not registered.'})

        # Generate a random verification code
        verification_code = str(random.randint(100000, 999999))  # 6-digit code

        # Create or update the EmailVerification record
        verification, created = EmailVerification.objects.update_or_create(
            email=email,
            defaults={'verification_code': verification_code, 'is_verified': False}
        )

        # Send verification email
        send_mail(
            'Your Verification Code',
            f'Your verification code is: {verification_code}',
            'your-email@example.com',  # Replace with your email
            [email],
            fail_silently=False,
        )

        return JsonResponse({'success': True, 'message': 'Verification code sent to your email!'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def verify_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Get the JSON data
        email = data.get('email')
        code = data.get('code')

        try:
            verification = EmailVerification.objects.get(email=email)

            if verification.verification_code == code:
                verification.is_verified = True
                verification.save()
                return JsonResponse({'success': True, 'message': 'Email verified successfully!'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid verification code.'})

        except EmailVerification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No verification record found for this email.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})




def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))


def request_withdrawal_code(request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        amount = data.get('amount')
        description = data.get('description')
        address = data.get('address')

        # Check if the user has enough balance
        if user.balance.main_balance < Decimal(amount):
            return JsonResponse({'success': False, 'message': 'Insufficient balance.'})

        # Check for an existing valid verification code
        existing_verification = VerificationCode.objects.filter(
            user=user,
            purpose='withdrawal',
            is_used=False,
            expires_at__gt=timezone.now()  # Check if the existing code has not expired
        ).first()

        if existing_verification:
            return JsonResponse({'success': False, 'message': 'A verification code is already active. Please use it or wait for it to expire.'})

        # Generate and save the new verification code
        verification_code = generate_verification_code()
        VerificationCode.objects.create(
            user=user,
            verification_code=verification_code,
            purpose='withdrawal',
            is_used=False,  # Ensure the new code is marked as unused
            expires_at=timezone.now() + timezone.timedelta(minutes=5)  # Set expiration time
        )

        # Send the verification code to the user's email
        send_mail(
            'Your Withdrawal Verification Code',
            f'Your code is: {verification_code}',
            'no-reply@example.com',  # Replace with your email or DEFAULT_FROM_EMAIL from settings
            [user.email],  # Adjust if the email field in your custom user model is different
            fail_silently=False,  # Change to True to suppress errors
        )

        return JsonResponse({'success': True, 'message': 'Verification code sent to your email.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})








def verify_withdrawal_code(request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        code = data.get('code')
        amount = Decimal(data.get('amount'))
        description = data.get('description', '')
        withdrawal_address = data.get('address', '')
        

        print(f"Received code: {code}, Amount: {amount}, Description: {description}, Withdrawal Address: {withdrawal_address}")

        # Find the latest valid verification code
        try:
            verification = VerificationCode.objects.get(
                user=user, 
                purpose='withdrawal', 
                is_used=False, 
                expires_at__gt=timezone.now(),
                verification_code=code
            )
        except VerificationCode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid or expired code.'})
        except VerificationCode.MultipleObjectsReturned:
            return JsonResponse({'success': False, 'message': 'Multiple verification codes found.'})

        # Log the found verification code for debugging
        print(f"Found verification: {verification.verification_code}, Expires at: {verification.expires_at}")

        # Check if the verification code is valid
        if verification:
            # Check if the user has enough balance
            if user.balance.main_balance >= amount:
                # Mark the verification code as used
                verification.is_used = True
                verification.save()

                # Deduct the amount from the user's balance
                user.balance.main_balance -= amount
                user.balance.save()

                # Log the withdrawal in the Withdrawal table
                withdrawal = Withdrawal.objects.create(
                    user=user,
                    amount=amount,
                    status='Pending',
                    description=description,
                    withdrawal_address=withdrawal_address
                )

                # Create a new transaction
                transaction = Transaction.objects.create(
                    user=user,
                    description=f'Withdrawal of {amount} USDT',
                    category='Withdrawal',
                    amount=amount,
                    status='Pending'
                )

                # Associate the transaction with the withdrawal
                withdrawal.transaction = transaction
                withdrawal.save()

                return JsonResponse({'success': True, 'message': 'Withdrawal successful.'})
            else:
                # Log the failed withdrawal due to insufficient balance
                withdrawal = Withdrawal.objects.create(
                    user=user,
                    amount=amount,
                    status='Failed',
                    description=description,
                    withdrawal_address=withdrawal_address
                )

                # Create a new transaction
                transaction = Transaction.objects.create(
                    user=user,
                    description=f'Failed withdrawal of {amount} USDT (Insufficient balance)',
                    category='Withdrawal',
                    amount=amount,
                    status='Failed'
                )

                # Associate the transaction with the withdrawal
                withdrawal.transaction = transaction
                withdrawal.save()

                return JsonResponse({'success': False, 'message': 'Insufficient balance.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})







def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))


def request_transfer_code(request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        amount = data.get('amount')
        description = data.get('description')
        receiver_wallet_address = data.get('address')
        transfer_type = data.get('transfer_type', 'USDT')  # Default to USDT if not provided
        usdt_type = data.get('usdt_type', 'TRC20')  # Default to TRC20 if not provided

        # Check if the user has enough balance
        if user.balance.main_balance < Decimal(amount):
            return JsonResponse({'success': False, 'message': 'Insufficient balance.'})

        # Check for an existing valid verification code
        existing_verification = VerificationCode.objects.filter(
            user=user,
            purpose='transfer',
            is_used=False,
            expires_at__gt=timezone.now()  # Check if the existing code has not expired
        ).first()

        if existing_verification:
            return JsonResponse({'success': False, 'message': 'A verification code is already active. Please use it or wait for it to expire.'})

        # Generate and save the new verification code
        verification_code = generate_verification_code()
        VerificationCode.objects.create(
            user=user,
            verification_code=verification_code,
            purpose='transfer',
            is_used=False,  # Ensure the new code is marked as unused
            expires_at=timezone.now() + timezone.timedelta(minutes=5)  # Set expiration time
        )

        # Send the verification code to the user's email
        send_mail(
            'Your Transfer Verification Code',
            f'Your code is: {verification_code}',
            'no-reply@example.com',  # Replace with your email or DEFAULT_FROM_EMAIL from settings
            [user.email],  # Adjust if the email field in your custom user model is different
            fail_silently=False,  # Change to True to suppress errors
        )

        return JsonResponse({'success': True, 'message': 'Verification code sent to your email.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})


def verify_transfer_code(request):
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        code = data.get('code')
        amount = Decimal(data.get('amount'))
        description = data.get('description', '')
        receiver_wallet_address = data.get('address', '')
        transfer_type = data.get('transfer_type', 'USDT')  # Default to USDT if not provided
        usdt_type = data.get('usdt_type', 'TRC20')  # Default to TRC20 if not provided

        print(f"Received code: {code}, Amount: {amount}, Description: {description}, Receiver Address: {receiver_wallet_address}")

        # Find the latest valid verification code
        try:
            verification = VerificationCode.objects.get(
                user=user, 
                purpose='transfer', 
                is_used=False, 
                expires_at__gt=timezone.now(),
                verification_code=code
            )
        except VerificationCode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid or expired code.'})
        except VerificationCode.MultipleObjectsReturned:
            return JsonResponse({'success': False, 'message': 'Multiple verification codes found.'})

        # Log the found verification code for debugging
        print(f"Found verification: {verification.verification_code}, Expires at: {verification.expires_at}")

        # Check if the verification code is valid
        if verification:
            # Check if the user has enough balance
            if user.balance.main_balance >= amount:
                # Mark the verification code as used
                verification.is_used = True
                verification.save()

                # Deduct the amount from the user's balance
                user.balance.main_balance -= amount
                user.balance.save()

                # Log the transfer in the Transfer table
                transfer = Transfer.objects.create(
                    sender=user,
                    receiver_wallet_address=receiver_wallet_address,
                    amount=amount,
                    description=description,
                    transfer_type=transfer_type,
                    usdt_type=usdt_type
                )

                # Create a new transaction
                transaction = Transaction.objects.create(
                    user=user,
                    description=f'Transfer of {amount} {transfer_type} to {receiver_wallet_address}',
                    category='Transfer',
                    amount=amount,
                    status='Pending'
                )

                # Associate the transaction with the transfer
                transfer.transaction = transaction
                transfer.save()

                return JsonResponse({'success': True, 'message': 'Transfer successful.'})
            else:
                # Log the failed transfer due to insufficient balance
                transfer = Transfer.objects.create(
                    sender=user,
                    receiver_wallet_address=receiver_wallet_address,
                    amount=amount,
                    status='Failed',
                    description=description
                )

                # Create a new transaction for the failed transfer
                transaction = Transaction.objects.create(
                    user=user,
                    description=f'Failed transfer of {amount} {transfer_type} (Insufficient balance)',
                    category='Transfer',
                    amount=amount,
                    status='Failed'
                )

                # Associate the transaction with the transfer
                transfer.transaction = transaction
                transfer.save()

                return JsonResponse({'success': False, 'message': 'Insufficient balance.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})




def confirm_transfer(request):
    transfer_id = request.GET.get('transfer_id')  # Get the transfer ID from the query parameter
    transfer = get_object_or_404(Transfer, id=transfer_id)  # Use the Transfer model

    if transfer.status == 'Pending':
        transfer.status = 'Completed'
        
        # Retrieve or create a transaction for the transfer
        transaction = Transaction.objects.filter(
            user=transfer.sender,
            amount=transfer.amount,
            category='Transfer',  # Ensure category matches the transfer
            status='Pending'
        ).first()

        if transaction:
            # Update the existing transaction status
            transaction.status = 'Completed'
            transaction.description = f"Transfer confirmed: {transfer.amount} USDT"
            transaction.save()  # Save changes to the transaction
        else:
            # Optionally create a new transaction if one does not exist
            transaction = Transaction.objects.create(
                user=transfer.sender,
                amount=transfer.amount,
                category='Transfer',
                status='Completed',
                description=f"Transfer confirmed: {transfer.amount} USDT"
            )

        transfer.save()  # Save the transfer status change
        messages.success(request, f"Transfer of {transfer.amount} confirmed successfully.")
    else:
        messages.warning(request, f"Transfer is already {transfer.status}.")

    return redirect('admin:accounts_transfer_changelist')  # Update this with the correct redirect path

# Decline transfer view
def decline_transfer(request):
    transfer_id = request.GET.get('transfer_id')  # Get the transfer ID from the query parameter
    transfer = get_object_or_404(Transfer, id=transfer_id)  # Use Transfer model

    if transfer.status == 'Pending':
        # Update transfer status
        transfer.status = 'Failed'

        # Retrieve the existing transaction for the transfer
        transaction = Transaction.objects.filter(
            user=transfer.sender,
            amount=transfer.amount,
            category='Transfer',  # Ensure category matches the transfer
            status='Pending'
        ).first()

        if transaction:
            # Update the existing transaction status
            transaction.status = 'Failed'
            transaction.description = f"Transfer declined: {transfer.amount} USDT"
            transaction.save()  # Save changes to the transaction
        else:
            messages.warning(request, "No pending transaction found to update.")

        transfer.save()  # Save the transfer status change
        messages.success(request, "Transfer has been declined.")
    else:
        messages.warning(request, f"Transfer is already {transfer.status}.")

    return redirect('admin:accounts_transfer_changelist') 




@login_required
def account_settings(request):
    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = AccountSettingsForm(instance=request.user)
    return render(request, 'dashboard/Accounts.html', {'form': form})




def toggle_daily_savings(request):
    if request.method == 'POST':
        try:
            # Get the most recent UserSavings entry for the user, based on the start_date
            user_savings = UserSavings.objects.filter(user=request.user).order_by('-start_date').first()

            if not user_savings:
                # If no savings exist, create a new entry
                user_savings = UserSavings.objects.create(
                    user=request.user,
                    amount=0.00,
                    profit_percentage=0.00,
                    start_date=timezone.now(),
                    payment_date=timezone.now() + timedelta(days=30),  # Example future payment date
                    is_daily_savings_active=False,
                    is_monthly_savings_active=False,
                    is_yearly_savings_active=False,
                )

            # Parse the incoming JSON request data
            data = json.loads(request.body)
            is_daily_savings_active = data.get('is_daily_savings_active', False)

            # Update the 'is_daily_savings_active' field for the specific entry
            user_savings.is_daily_savings_active = is_daily_savings_active
            user_savings.save()

            return JsonResponse({'success': True})
        
        except Exception as e:
            # Log and return error in case of any issues
            print(e)
            return JsonResponse({'success': False, 'error': str(e)})

    # Return an error for non-POST requests
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def withdraw_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = Decimal(data.get('amount'))  # Convert the amount to Decimal
            user = request.user  # Ensure the user is authenticated

            # Retrieve user savings (only those with daily savings active)
            user_savings = UserSavings.objects.filter(user=user, is_daily_savings_active=True).first()
            balance = Balance.objects.get(user=user)

            # Check if user savings exist and user has sufficient savings
            if user_savings and user_savings.amount >= amount and balance.daily_savings >= amount:
                # Update user savings amount
                user_savings.amount -= amount  # Deduct from user_savings amount
                user_savings.save()

                # Update daily savings in balance
                balance.daily_savings -= amount  # Deduct from daily savings
                balance.total_savings -= amount
                balance.save()

                # Update main balance
                balance.main_balance += amount  # Add to main balance
                balance.save()

                # Create a transaction for the withdrawal in the Transaction model
                transaction = Transaction.objects.create(
                    user=user,
                    amount=amount,
                    category='daily savings Withdrawal',
                    status='Completed',
                    description=f'Withdrawal of ${amount} from daily savings',
                )

                return JsonResponse({'success': True, 'new_balance': balance.main_balance})

            else:
                return JsonResponse({'success': False, 'error': 'Insufficient funds in savings or daily savings.'}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)





@login_required
@require_http_methods(['POST'])
def save_monthly_savings(request):
    try:
        # Parse the JSON request data
        data = json.loads(request.body)
        amount = data.get('amount')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Validate input data
        if not amount or not start_date or not end_date:
            return JsonResponse({'success': False, 'error': 'Invalid input data'})

        # Convert amount to Decimal
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})

        # Get the user's balance
        try:
            balance = Balance.objects.get(user=request.user)
        except Balance.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User  balance not found'})

        # Get the savings percentage
        savings_percentage = SavingsPercentage.objects.first()
        if not savings_percentage:
            return JsonResponse({'success': False, 'error': 'Savings percentage not set'})

        # Calculate the savings amount based on the percentage
        savings_amount = (amount * savings_percentage.monthly_savings_percentage) / Decimal('100.00')

        # Check if the user has enough balance
        if balance.main_balance < savings_amount:
            return JsonResponse({'success': False, 'error': 'Insufficient balance'})

        # Deduct the savings amount from the main balance
        balance.main_balance -= savings_amount
        balance.monthly_savings += savings_amount
        balance.total_savings += savings_amount
        balance.save()

        # Create a UserSavings record
        UserSavings.objects.create(
            user=request.user,
            amount=savings_amount,
            profit_percentage=savings_percentage.monthly_savings_percentage,
            start_date=start_date,
            payment_date=end_date,
            is_monthly_savings_active=True
        )

        # Create a Transaction record
        Transaction.objects.create(
            user=request.user,
            description='Monthly savings deduction',
            category='Savings',
            amount=savings_amount,
            status='Completed'
        )

        return JsonResponse({'success': True, 'message': 'Monthly savings saved successfully.'})

    except Exception as e:
        print(e)
        return JsonResponse({'success': False, 'error': str(e)})
    
    
    


@login_required
@require_http_methods(['POST'])
def save_yearly_savings(request):
    try:
        # Parse the JSON request data
        data = json.loads(request.body)
        amount = data.get('amount')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Validate input data
        if not amount or not start_date or not end_date:
            return JsonResponse({'success': False, 'error': 'Invalid input data'})

        # Convert amount to Decimal
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})

        # Get the user's balance
        try:
            balance = Balance.objects.get(user=request.user)
        except Balance.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User  balance not found'})

        # Get the savings percentage
        savings_percentage = SavingsPercentage.objects.first()
        if not savings_percentage:
            return JsonResponse({'success': False, 'error': 'Savings percentage not set'})

        # Calculate the savings amount based on the percentage
        savings_amount = (amount * savings_percentage.yearly_savings_percentage) / Decimal('100.00')

        # Check if the user has enough balance
        if balance.main_balance < savings_amount:
            return JsonResponse({'success': False, 'error': 'Insufficient balance'})

        # Deduct the savings amount from the main balance
        balance.main_balance -= savings_amount
        balance.yearly_savings += savings_amount
        balance.total_savings += savings_amount
        balance.save()

        # Create a UserSavings record
        UserSavings.objects.create(
            user=request.user,
            amount=savings_amount,
            profit_percentage=savings_percentage.yearly_savings_percentage,
            start_date=start_date,
            payment_date=end_date,
            is_yearly_savings_active=True
        )

        # Create a Transaction record
        Transaction.objects.create(
            user=request.user,
            description='Yearly savings deduction',
            category='Savings',
            amount=savings_amount,
            status='Completed'
        )

        return JsonResponse({'success': True, 'message': 'Monthly savings saved successfully.'})

    except Exception as e:
        print(e)
        return JsonResponse({'success': False, 'error': str(e)})    
    





