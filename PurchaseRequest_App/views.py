from django.shortcuts import render
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Approval, PurchaseRequest, AuditLog
from .forms import PurchaseRequestForm, ApprovalForm, UserProfileForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
import uuid
from django.conf import settings
from .models import request_officerProfile, managerProfile, UserProfile
from datetime import datetime
from django.contrib.auth import logout

# define the views for the Purchase Request App
@login_required
def home(request):
    return render(request, 'PurchaseRequest_App/home.html')

@login_required
def request_list(request):
    if request.user.userprofile.user_type == 'manager':
        requests = PurchaseRequest.objects.all()
    else:
        requests = PurchaseRequest.objects.filter(requester=request.user)
    return render(request, 'PurchaseRequest_App/request_list.html', {'requests': requests})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

@login_required
def request_create(request):
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, request.FILES)
        if form.is_valid():
            purchase_request = form.save(commit=False)
            purchase_request.requester = request.user
            purchase_request.save()
            AuditLog.objects.create(
                request=purchase_request,
                user=request.user,
                action='CREATED',
                details=f"Created request for {purchase_request.item}"
            )
            messages.success(request, 'Purchase request submitted successfully!')
            return redirect('request_list')
    else:
        form = PurchaseRequestForm()
    return render(request, 'PurchaseRequest_App/request_form.html', {'form': form})

@login_required
def request_approve(request, request_id):
    if not request.user.is_manager:
        raise PermissionDenied("Only managers can approve requests.")
    pr = get_object_or_404(PurchaseRequest, id=request_id)
    if pr.status != 'PENDING':
        messages.error(request, 'This request is no longer pending.')
        return redirect('request_list')
    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.request = pr
            approval.manager = request.user
            approval.save()
            pr.status = 'APPROVED' if approval.approved else 'REJECTED'
            pr.save()
            AuditLog.objects.create(
                request=pr,
                user=request.user,
                action='APPROVED' if approval.approved else 'REJECTED',
                details=f"{'Approved' if approval.approved else 'Rejected'} with comments: {approval.comments}"
            )
            messages.success(request, f'Request {pr.item} has been {"approved" if approval.approved else "rejected"}.')
            return redirect('request_list')
    else:
        form = ApprovalForm()
    return render(request, 'PurchaseRequest_App/approve_form.html', {'request': pr, 'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                AuditLog.objects.create(  # request is not needed here
                    user=user,
                    action='LOGIN',
                    details=f"User {user.username} logged in."
                )
                return redirect('home')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'PurchaseRequest_App/login.html', {'form': form})


def generate_request_id():
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def signup_view(request):
    User = get_user_model()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        #request_id = request.POST.get('request_id')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_manager = request.POST.get('is_manager') == 'on'

        errors = []
        if not username or not email or not phone_number or not password1 or not password2:
            errors.append("All fields are required.")
        if password1 != password2:
            errors.append("Passwords do not match.")

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        if User.objects.filter(email=email).exists():
            errors.append("Email already exists.")

        if errors:
            return render(request, 'PurchaseRequest_App/signup.html', {
                'errors': errors,
                'username': username,
                'email': email,
                'phone_number': phone_number,
                'is_manager': is_manager,
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            #request_id=generate_request_id()
        )

        # Create a user profile
        profile = user.profile(username=username, email=email, password=password1, is_manager=is_manager,
                               phone_number=phone_number)
        profile.save()
        
        # Automatically log in the user after signup
        login(request, user)
        AuditLog.objects.create(
            request=None,
            user=user,
            action='SIGNUP',
            details=f"User {user.username} signed up."
        )
        return redirect('home')
    else:
        return render(request, 'PurchaseRequest_App/signup.html')
    
@login_required(login_url='/PurchaseRequest_App/login')

def profile(request):
    user = request.user

    if user.userprofile.user_type == 'manager':
        try:
            profile = managerProfile.objects.get(user=user)
            approves = Approval.objects.filter(manager=profile)
            context = { # Context for rendering the manager profile
                'profile': profile,
                'approves': approves,
            }
            return render(request, 'PurchaseRequest_App/manager_profile.html', context)
        except:
            return redirect('create_managerProfile')
    elif user.userprofile.user_type == 'request_officer': # Handle request officer profile
        try:
            profile = request_officerProfile.objects.get(user=user)
            requests = PurchaseRequest.objects.filter(requester=profile.user)
            context = {
                'profile': profile,
                'requests': requests,
            }
            return render(request, 'PurchaseRequest_App/officer_profile.html', context)
        except:
            return redirect('create_officerProfile')
        
    else:
        # Handle other user or error case
        return render(request, 'PurchaseRequest_App/unknown_profile.html')
    
@login_required(login_url='/PurchaseRequest_App/login')
def create_officerProfile(request):
    try: 
        profile = request_officerProfile.objects.get(user=request.user)
        return redirect('officer_profile')

    except:
        GENDER_CHOICES = [
            ('M', 'Male'),
            ('F', 'Female'),
            ('O', 'Other'),
        ]
        if request.method == 'POST': # Handle form submission
            name = request.POST.get('name')
            address = request.POST.get('address')
            phone_number = request.POST.get('phone_number')
            position_title = request.POST.get('position_title')
            email = request.POST.get('email')
            employee_id = request.POST.get('employee_id')
            department = request.POST.get('department')
            profile_picture = request.FILES.get('profile_picture')

            profile = request_officerProfile(
                user=request.user,
                name=name,
                address=address,
                phone_number=phone_number,
                position_title=position_title,
                email=email,
                employee_id=employee_id,
                department=department,
                profile_picture=profile_picture,
            )
            profile.save()
            return redirect('profile')
        
        context = {
            'GENDER_CHOICES': GENDER_CHOICES,
        }
        return render(request, 'PurchaseRequest_App/create_officerProfile.html', context)
        
def create_managerProfile(request):
    GENDER_CHOICES = managerProfile.GENDER_CHOICES
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        position_title = request.POST.get('position_title')
        email = request.POST.get('email')
        employee_id = request.POST.get('employee_id')
        department = request.POST.get('department')
        profile_picture = request.FILES.get('profile_picture')
        gender = request.POST.get('gender')

        manager = managerProfile(
            user=request.user,
            name=name,
            address=address,
            phone_number=phone_number,
            position_title=position_title,
            email=email,
            employee_id=employee_id,
            department=department,
            gender=gender,
            profile_picture=profile_picture,
        )
        manager.save()
        return redirect('profile')
    context = {
        'GENDER_CHOICES':GENDER_CHOICES
    }
    return render(request, 'PurchaseRequest_App/create_managerProfile.html', context)
                                               
def my_view(request):
    UserProfile.objects.get_or_create(user=request.user)
    # ...rest of your code...

@login_required
def profile_detail(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'profile_detail.html', {'profile': profile})

@login_required
def profile_update(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'profile_form.html', {'form': form})

def year(request):
    return {'year': datetime.now().year}

