from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from accounts.models import Account


class RegistrationForm(UserCreationForm):
    fullname = forms.CharField(max_length=100, help_text='Required. Enter your full name')
    email = forms.EmailField(max_length=100, help_text='Required. Add a valid email address')

    class Meta:
        model = Account
        fields = ("fullname", "username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control form-control-bg'  # Use Bootstrap small size
            field.widget.attrs['style'] = 'border: 1px solid black;'
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Account.objects.filter(username=username).exists():
            raise forms.ValidationError('This username has been taken')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.fullname = self.cleaned_data['fullname']
        user.country = 'Not set'
        if commit:
            user.save()
        return user


class AccountAuthenticationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ('email', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control form-control-bg'  # Use Bootstrap small size
            field.widget.attrs['style'] = 'border: 1px solid black;'

    def clean(self):
        if self.is_valid():
            cleaned_data = super().clean()
            email = cleaned_data.get("email")
            password = cleaned_data.get("password")
            if email and password:
                user = authenticate(email=email, password=password)
                if not user:
                    raise forms.ValidationError('Invalid login credentials')
            return cleaned_data
        
        
class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Enter your email address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control border-none',  # Bootstrap class for styling
            'placeholder': 'example@example.com',
            'style': 'border: 1px solid black;'# Placeholder text
        }),
        error_messages={
            'required': 'This field is required.',
            'invalid': 'Enter a valid email address.',
        }
    )  
       


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['username','country', 'phone']  # Include the fields you want to update
             

              

