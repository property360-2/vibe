from django.contrib import admin
from .models import MembershipPlan, Member, MembershipPass, Attendance


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'price', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'created_at']
    search_fields = ['name', 'phone']


@admin.register(MembershipPass)
class MembershipPassAdmin(admin.ModelAdmin):
    list_display = ['member', 'membership_plan', 'start_date', 'end_date', 'price_snapshot', 'status']
    list_filter = ['status', 'membership_plan']
    search_fields = ['member__name']
    date_hierarchy = 'start_date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['member', 'membership_pass', 'checked_in_at']
    list_filter = ['checked_in_at']
    search_fields = ['member__name']
    date_hierarchy = 'checked_in_at'
