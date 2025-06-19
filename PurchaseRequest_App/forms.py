from django import forms
from django.contrib.auth.models import User
from .models import PurchaseRequest, Approval, UserProfile
from django.conf import settings
from django.core.mail import send_mail

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['item', 'description', 'amount', 'document']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

class ApprovalForm(forms.ModelForm):
    class Meta:
        model = Approval
        fields = ['approved', 'comments']

class SignUpForm(forms.Form):
    #request_id = forms.IntegerField(required=False, label="Request ID")
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")
    is_manager = forms.BooleanField(required=False, label="Register as Manager")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        confirm_password = cleaned_data.get("confirm_password")
        if password1 and confirm_password and password1 != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email
    
    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        phone_number = self.cleaned_data['phone_number']
        password = self.cleaned_data['password1']
        is_manager = self.cleaned_data.get('is_manager', False)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.profile.phone_number = phone_number
        user.profile.is_manager = is_manager
        # Generate verification code
        verification_code = User.objects.make_random_password(length=6, allowed_chars='0123456789')
            
            # Add the verification code to cleaned_data 
        self.cleaned_data['verification_code'] = verification_code
    
            # Send verification email
        self.send_verification_email(self.cleaned_data, verification_code)
    
        user.profile.save()
            
        return user
    
    def send_verification_email(self, cleaned_data, verification_code):
            username = cleaned_data['username']
            email = cleaned_data['email']

            subject = 'Verification Code'
            message = f'Hello {username},\n\nYour verification code is: {verification_code}' # The verification code is sent to the user
            from_email = settings.DEFAULT_FROM_EMAIL

            send_mail(subject, message, from_email, [email], fail_silently=False)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user_type']  # Add or remove fields as needed
