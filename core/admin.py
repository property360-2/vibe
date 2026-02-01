from django.contrib import admin
from .models import (
    MembershipPlan, Member, MembershipPass, Attendance,
    CustomerProfile, Workout, WorkoutExercise, Achievement, CustomerAchievement
)


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


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['member', 'age', 'experience', 'primary_goal', 'is_active', 'updated_at']
    list_filter = ['experience', 'primary_goal', 'training_days', 'is_active']
    search_fields = ['member__name', 'member__user__username']


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 1


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty', 'goal_type', 'is_active', 'created_at']
    list_filter = ['difficulty', 'goal_type', 'is_active']
    search_fields = ['name', 'description']
    inlines = [WorkoutExerciseInline]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']


@admin.register(CustomerAchievement)
class CustomerAchievementAdmin(admin.ModelAdmin):
    list_display = ['member', 'achievement', 'unlocked_at']
    list_filter = ['achievement', 'unlocked_at']
    search_fields = ['member__name', 'achievement__name']
