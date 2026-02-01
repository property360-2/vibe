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
    path('members/sell-pass/', views.sell_pass, name='sell_pass'),
    path('members/check-duplicate/', views.check_duplicate_member, name='check_duplicate_member'),
    
    # Passes
    # Passes
    # path('passes/', views.passes_list, name='passes_list'),
    
    # Attendance
    # path('attendance/', views.attendance_list, name='attendance_list'),
    
    # Reports
    path('reports/', views.reports, name='reports'),

    # Customer Portal
    path('my-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('my-transactions/', views.customer_transactions, name='customer_transactions'),
    path('my-reports/', views.customer_reports, name='customer_reports'),
    path('my-personalization/', views.customer_personalization, name='customer_personalization'),
    path('my-workouts/', views.workout_library, name='workout_library'),
    path('my-workouts/<int:pk>/', views.workout_detail, name='workout_detail'),
    path('attendance/in/<int:pk>/', views.check_in_member, name='check_in_member'),
    path('attendance/out/<int:pk>/', views.check_out_member, name='check_out_member'),
    path('my-dashboard/password/', views.change_password, name='change_password'),
]
