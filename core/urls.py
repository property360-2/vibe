from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),
    
    # Membership Plans
    path('plans/', views.plans_list, name='plans_list'),
    path('plans/<int:pk>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:pk>/delete/', views.plan_delete, name='plan_delete'),
    
    # Members
    path('members/', views.members_list, name='members_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    
    # Passes
    path('passes/', views.passes_list, name='passes_list'),
    
    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
]
