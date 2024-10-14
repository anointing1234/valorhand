from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal



class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")
        if not username:
            raise ValueError("User must have a username")

        email = self.normalize_email(email)  # Normalize the email to lowercase
        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)  # Set the user's password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        # Ensure superuser has necessary flags set
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Ensure superuser must have an email and username
        user = self.create_user(email, username, password, **extra_fields)
        return user

class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email", max_length=100, unique=True)
    username = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)  # Update on login
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    fullname = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, default='Not set')  # Default value
    country = models.CharField(max_length=50, default='Not set')  # Default value
    # profile_picture = models.ImageField(upload_to='media/profile_pics/', default='media/profile_pics/profile_odj.jpg')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = AccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Check permissions for the user."""
        return self.is_admin

    def has_module_perms(self, app_label):
        """Check module permissions for the user."""
        return True

class Balance(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Normal balances
    main_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.000)
    
    # Total and savings
    total_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.000)
    daily_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.000)
    monthly_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.000)
    yearly_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.000)


    def __str__(self):
        return f"{self.user.username}'s Balance"



class SavingsPercentage(models.Model):
    daily_savings_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Enter percentage for daily savings")
    monthly_savings_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Enter percentage for monthly savings")
    yearly_savings_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Enter percentage for yearly savings")

    def __str__(self):
        return "Savings Percentages"

    class Meta:
        verbose_name = "Savings Percentage"
        verbose_name_plural = "Savings Percentages" 



class UserSavings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # The amount saved by the user
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Profit percentage that applies to the savings
    profit_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Start date, set to the current date when the savings entry is created
    start_date = models.DateField(default=timezone.now)
    
    # Payment date when the savings and profit will be paid to the user
    payment_date = models.DateField()
    
    # New field to track daily savings activation
    is_daily_savings_active = models.BooleanField(default=False)
    # New field to track daily savings activation
    is_monthly_savings_active = models.BooleanField(default=False)
    # New field to track daily savings activation
    is_yearly_savings_active = models.BooleanField(default=False)



    def __str__(self):
        return f"Savings for {self.user.username}"

    class Meta:
        verbose_name = "User Savings"
        verbose_name_plural = "Users' Savings"




           

import uuid
    
class Transaction(models.Model):
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateTimeField(auto_now_add=True)  # Date when the transaction was made
    description = models.CharField(max_length=255)  # Description of the transaction
    category = models.CharField(max_length=50)  # Category (e.g., Deposit, Withdrawal, Loan Payment, etc.)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # Amount involved in the transaction
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')])

    class Meta:
        ordering = ['-date']  # Orders transactions by date, with the latest first

    def __str__(self):
        return f"Transaction - {self.user.username} - {self.status}"


class Deposit(models.Model):
    TRANSACTION_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Declined', 'Declined')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='Pending')
    
    # Allow any text input for balance_type by removing the choices parameter
    balance_type = models.CharField(max_length=50, default='Deposit')  # Increase max_length if needed

    def __str__(self):
        return f"{self.user} - {self.amount}"


class Withdrawal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ], default='Pending')
    description = models.CharField(max_length=255, blank=True)

    # Added withdrawal_address field
    withdrawal_address = models.CharField(max_length=255, blank=True)  # Adjust max_length as needed

    BALANCE_TYPE_CHOICES = [
        ('Withdrawal', 'Withdrawal')
    ]
    balance_type = models.CharField(max_length=10, choices=BALANCE_TYPE_CHOICES, default='Withdrawal')

    def __str__(self):
        return f"Withdrawal {self.user.username} - {self.amount} - {self.status}"



class VerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
    ]
    
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='verification_codes')
    verification_code = models.CharField(max_length=6)  # Assuming a 6-digit code
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set the expiration time (e.g., 10 minutes from creation)
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        # Check if the code has expired
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {'Used' if self.is_used else 'Not Used'}"



class DepositAddress(models.Model):
    WALLET_TYPE_CHOICES = [
        ('TRC20', 'TRC20'),
        ('ERC20', 'ERC20'),
    ]

    wallet_type = models.CharField(max_length=10, choices=WALLET_TYPE_CHOICES,default="TRC20")
    usdt_wallet_address = models.CharField(max_length=100,default="djkjsajskjsk")

    class Meta:
        unique_together = ('wallet_type', 'usdt_wallet_address')  # Ensure wallet addresses are unique by type

    def __str__(self):
        return f"{self.wallet_type} USDT Wallet Address: {self.usdt_wallet_address}"


class Transfer(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfers')  # User who initiates the transfer
    receiver_wallet_address = models.CharField(max_length=100)  # Receiver's USDT wallet address
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Amount to transfer
    date = models.DateTimeField(auto_now_add=True)  # Date when the transfer is made
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ], default='Pending')
    description = models.CharField(max_length=255, blank=True)  # Optional description
    
    TRANSFER_TYPE_CHOICES = [
        ('USDT', 'USDT')
    ]
    USDT_TYPE_CHOICES = [  # Renamed to follow the convention
        ('TRC20', 'TRC20'),
        ('ERC20', 'ERC20'),
    ]
    transfer_type = models.CharField(max_length=10, choices=TRANSFER_TYPE_CHOICES, default='USDT')
    usdt_type = models.CharField(max_length=10, choices=USDT_TYPE_CHOICES, default='TRC20')  # New field for USDT type

    def __str__(self):
        return f"Transfer by {self.sender.username} to {self.receiver_wallet_address} - {self.amount} USDT - {self.status}"
    
    
class EmailVerification(models.Model):
    email = models.EmailField(max_length=254, unique=True)  # Email address to be verified
    verification_code = models.CharField(max_length=6)  # Verification code sent to the user
    is_verified = models.BooleanField(default=False)  # Flag indicating whether the email is verified
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the verification was created

    def __str__(self):
        return f"Email Verification for {self.email}"  