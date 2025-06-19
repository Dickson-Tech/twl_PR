
# Register your models here.
from django.contrib import admin
from .models import PurchaseRequest, Approval, AuditLog, User

#@admin.register(User)
#class UserAdmin(admin.ModelAdmin):
   # list_display = ('user', 'user_type', 'phone_number', 'department', 'is_manager')
    #search_fields = ('user__username', 'user__email', 'department')

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('item', 'requester', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('item', 'description')
    date_hierarchy = 'created_at'

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('manager', 'approved', 'created_at')
    list_filter = ('approved', 'created_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')