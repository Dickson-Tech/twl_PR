from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail


# PurchaseRequest_App/models.py

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=50, default='nothing')
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class managerProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'), 
        ('F', 'Female'), 
        ('O', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100, default="")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="")
    phone_number = models.CharField(max_length=15, default="")
    address = models.TextField(max_length=100,default="")
    department = models.CharField(max_length=100, default="")
    profile_picture = models.ImageField(upload_to='manager_profile_pictures/', default='default.jpg')
    email = models.EmailField(max_length=254, default="")
    employee_id = models.CharField(max_length=20, default="")
    position_title = models.CharField(max_length=100, default="")
    #date_of_joining = models.DateField(null=True, blank=True)
    #date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class request_officerProfile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
     GENDER_CHOICES = [
        ('M', 'Male'), 
        ('F', 'Female'), 
        ('O', 'Other'),
    ]
     name = models.CharField(max_length=100, default="")
     address = models.TextField(max_length=100,default="")
     phone_number = models.CharField(max_length=15, default="")
     derpartment = models.CharField(max_length=100, default="")
     profile_picture = models.ImageField(upload_to='profile_pictures/', default='default.jpg')
     gender = models.CharField(max_length=1, choices =GENDER_CHOICES, default="")
     position_title = models.CharField(max_length=100, default="")
     email = models.EmailField(max_length=254, default="")
     employee_id = models.CharField(max_length=20, default="")

     def __str__(self):
         return self.user.username  

class PurchaseRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    #request_id = models.IntegerField(null=True, blank=True)  # Allow NULL
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    item = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    document = models.FileField(upload_to='documents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item} - {self.requester.username}"

    def save(self, *args, **kwargs):
        if self.pk:  # If updating an existing request
            old_status = PurchaseRequest.objects.get(pk=self.pk).status
            if old_status != self.status:
                self.notify_status_change()
        super().save(*args, **kwargs)

    def notify_status_change(self):
        subject = f"Purchase Request {self.item} - Status Update"
        message = (
            f"Dear {self.requester.username},\n\n"
            f"Your purchase request for '{self.item}' has been {self.status.lower()}.\n"
            f"Amount: ${self.amount}\n"
            f"Check the portal for more details.\n\n"
            f"Best regards,\nPurchase Request Team"
        )
        send_mail(
            subject,
            message,
            'from@example.com',
            [self.requester.email],
            fail_silently=False,
        )

class Approval(models.Model):
    #request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='approvals')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approvals')
    approved = models.BooleanField(null=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Approval for {self.request.item} by {self.manager.username}"

class AuditLog(models.Model):
    #request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} on {self.request.item} by {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)