from django.urls import path
from django.contrib import admin
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/new/', views.request_create, name='request_create'),
    path('requests/<int:request_id>/approve/', views.request_approve, name='request_approve'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('officer_profile/', views.create_officerProfile, name='create_officerProfile'),
    path('manager_profile/', views.create_managerProfile, name='create_managerProfile'),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('profile/edit/', views.profile_update, name='profile_update'),
    path('logout/', views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)