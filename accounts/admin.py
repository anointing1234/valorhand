from django.utils.html import format_html
from django.contrib import admin
from .models import Account, Balance, Transaction, Deposit, Withdrawal,DepositAddress,Transfer,EmailVerification,VerificationCode,SavingsPercentage,UserSavings 
from django.urls import reverse

class AccountAdmin(admin.ModelAdmin):
    # Define the fields to display in the list view
    list_display = (
        'email', 'username', 'fullname', 'country', 'is_active', 
        'is_staff', 'is_admin', 'date_joined', 'last_login'
    )
    search_fields = ('email', 'username', 'fullname', 'country')
    readonly_fields = ('date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_admin', 'date_joined', 'last_login', 'country')  
    ordering = ('-date_joined',)  
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'fullname', 'phone', 'country','password')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser')
        }),
        ('Dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )

   


class BalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'main_balance', 'total_savings', 'daily_savings', 'monthly_savings', 'yearly_savings')
    search_fields = ('user__username', 'user__email')  # Searchable fields
    readonly_fields = ('user',)  # Make the user field read-only

    fieldsets = (
        (None, {
            'fields': ('user', 'main_balance', 'total_savings', 'daily_savings', 'monthly_savings', 'yearly_savings')
        }),
    )

    def has_add_permission(self, request):
        return False  # Disable the add button

    def has_delete_permission(self, request, obj=None):
        return False  # Disable the delete button

    
class TransactionAdmin(admin.ModelAdmin):
    # Define fields to show in the list display
    list_display = (
         'user', 'date', 'description', 'category', 
        'amount_display','status'
    )
    list_filter = ('status', 'category', 'date')  # Filter options for better navigation
    search_fields = ('user__username', 'user__email','description')  # Search fields

    # Format amount and balance fields
    def amount_display(self, obj):
        if obj.amount is not None:
            return f"${obj.amount:,.2f}"
        return "N/A"
    amount_display.short_description = 'Amount'

  
    # Enable ordering by date (newest first)
    ordering = ('-date',)


class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'status', 'balance_type', 'confirm_button', 'decline_button')
    list_filter = ('status', 'balance_type')
    search_fields = ('user__username',)

    def confirm_button(self, obj):
        if obj.status == 'Pending':
            return format_html(
                '<a class="btn btn-primary" href="{}">Confirm</a>',
                reverse('confirm_deposit') + f'?deposit_id={obj.pk}'  # Use GET parameter
            )
        return ''
    
    def decline_button(self, obj):
        if obj.status == 'Pending':
            return format_html(
                '<a class="btn btn-danger" href="{}">Decline</a>',
                reverse('decline_deposit') + f'?deposit_id={obj.pk}'  # Use GET parameter
            )
        return ''

    confirm_button.short_description = 'Confirm'
    decline_button.short_description = 'Decline'



class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'status', 'balance_type', 'withdrawal_address', 'confirm_button', 'decline_button')
    list_filter = ('status', 'balance_type')
    search_fields = ('user__username',)

    def confirm_button(self, obj):
        if obj.status == 'Pending':
            return format_html(
                '<a class="btn btn-primary" href="{}">Confirm</a>',
                reverse('confirm_withdrawal') + f'?withdrawal_id={obj.pk}'  # Use GET parameter
            )
        return ''
    
    def decline_button(self, obj):
        if obj.status == 'Pending':
            return format_html(
                '<a class="btn btn-danger" href="{}">Decline</a>',
                reverse('decline_withdrawal') + f'?withdrawal_id={obj.pk}'  # Use GET parameter
            )
        return ''

    confirm_button.short_description = 'Confirm'
    decline_button.short_description = 'Decline'


class TransferAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver_wallet_address', 'amount', 'date', 'status', 'transfer_type', 'usdt_type', 'confirm_button', 'decline_button')
    list_filter = ('status', 'transfer_type', 'usdt_type')
    search_fields = ('sender__username', 'receiver_wallet_address')

    def confirm_button(self, obj):
        if obj.status == 'Pending':
            return format_html(
                '<a class="btn btn-primary" href="{}">Confirm</a>',
                reverse('confirm_transfer') + f'?transfer_id={obj.pk}'  # Use GET parameter
            )
        return ''
    
    def decline_button(self, obj):
        if obj.status == 'Pending':
            return format_html(
                '<a class="btn btn-danger" href="{}">Decline</a>',
                reverse('decline_transfer') + f'?transfer_id={obj.pk}'  # Use GET parameter
            )
        return ''

    confirm_button.short_description = 'Confirm'
    decline_button.short_description = 'Decline'



class DepositAddressAdmin(admin.ModelAdmin):
    list_display = ('wallet_type', 'usdt_wallet_address')
    list_filter = ('wallet_type',)
    search_fields = ('usdt_wallet_address',)

    def has_add_permission(self, request):
        # Check if at least one deposit address already exists
        if DepositAddress.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of deposit addresses
        return False    
    

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('email',)



class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_code', 'purpose', 'is_used', 'created_at', 'expires_at')
    list_filter = ('purpose', 'is_used')




@admin.register(SavingsPercentage)
class SavingsPercentageAdmin(admin.ModelAdmin):
    list_display = ('daily_savings_percentage', 'monthly_savings_percentage', 'yearly_savings_percentage')
    list_editable = ('daily_savings_percentage', 'monthly_savings_percentage', 'yearly_savings_percentage')
    list_display_links = None  # No clickable link, since all fields are editable

    fieldsets = (
        (None, {
            'fields': ('daily_savings_percentage', 'monthly_savings_percentage', 'yearly_savings_percentage')
        }),
    )

    # Only allow adding or editing one instance
    def has_add_permission(self, request):
        # Allow adding only if no instance exists
        if SavingsPercentage.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the object
        return False

@admin.register(UserSavings)
class UserSavingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'profit_percentage', 'start_date', 'payment_date', 
                    'is_daily_savings_active', 'is_monthly_savings_active', 'is_yearly_savings_active')
    search_fields = ('user__username',)






admin.site.register(VerificationCode, VerificationCodeAdmin)      
admin.site.register(EmailVerification, EmailVerificationAdmin)    
admin.site.register(Transfer, TransferAdmin)    
admin.site.register(Withdrawal, WithdrawalAdmin)
admin.site.register(Deposit, DepositAdmin)
admin.site.register(Balance, BalanceAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(DepositAddress, DepositAddressAdmin)


