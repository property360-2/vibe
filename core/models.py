from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSetting.objects.create(user=instance)

class UserSetting(models.Model):
    """UI Preferences for any user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    theme = models.CharField(max_length=10, default='dark', choices=[('dark', 'Dark Mode'), ('light', 'Light Mode')])
    font_size = models.CharField(max_length=10, default='medium', choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')])

    def __str__(self):
        return f"{self.user.username}'s Settings"

class MembershipPlan(models.Model):
    """Configurable membership plans for the gym"""
    name = models.CharField(max_length=100)
    duration_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['duration_days']

    def __str__(self):
        return f"{self.name} ({self.duration_days} days - ₱{self.price})"


class Member(models.Model):
    """Gym members who purchase walk-in passes"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_active_pass(self):
        """Get the member's currently active pass"""
        today = timezone.now().date()
        return self.passes.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='active'
        ).first()

    def has_active_pass(self):
        """Check if member has an active pass"""
        return self.get_active_pass() is not None


class MembershipPass(models.Model):
    """Purchased membership passes"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='passes')
    membership_plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name='passes')
    start_date = models.DateField()
    end_date = models.DateField()
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Membership Passes'

    def __str__(self):
        return f"{self.member.name} - {self.membership_plan.name} ({self.status})"

    def save(self, *args, **kwargs):
        """Auto-calculate end_date and snapshot price on creation"""
        if not self.pk:  # Only on creation
            if not self.start_date:
                self.start_date = timezone.now().date()
            if not self.end_date:
                self.end_date = self.start_date + timedelta(days=self.membership_plan.duration_days - 1)
            if not self.price_snapshot:
                self.price_snapshot = self.membership_plan.price
        super().save(*args, **kwargs)

    def update_status(self):
        """Update status based on current date"""
        today = timezone.now().date()
        if today > self.end_date and self.status == 'active':
            self.status = 'expired'
            self.save(update_fields=['status'])

    @property
    def is_valid(self):
        """Check if pass is currently valid"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status == 'active'

    @property
    def days_remaining(self):
        """Get days remaining on the pass"""
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days + 1


class Attendance(models.Model):
    """Daily check-ins"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendances')
    membership_pass = models.ForeignKey(MembershipPass, on_delete=models.SET_NULL, null=True, blank=True)
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-checked_in_at']

    def __str__(self):
        return f"{self.member.name} - {self.checked_in_at.strftime('%Y-%m-%d %H:%M')}"


class CustomerProfile(models.Model):
    """Extended profile for members to track stats and preferences"""
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    TRAINING_DAYS_CHOICES = [
        (1, '1 Day'), (2, '2 Days'), (3, '3 Days'),
        (4, '4 Days'), (5, '5 Days'), (6, '6 Days'),
    ]
    GOAL_CHOICES = [
        ('muscle_gain', 'Muscle Gain'),
        ('fat_loss', 'Fat Loss'),
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('general', 'General Fitness'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES)
    training_days = models.IntegerField(choices=TRAINING_DAYS_CHOICES)
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    savage_mode = models.BooleanField(default=False)

    weekly_schedule = models.JSONField(default=dict, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    theme = models.CharField(max_length=10, default='dark', choices=[('dark', 'Dark Mode'), ('light', 'Light Mode')])
    font_size = models.CharField(max_length=10, default='medium', choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')])

    def __str__(self):
        return f"{self.member.name}'s Profile"


class Workout(models.Model):
    """Hardcoded workout library entries"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    GOAL_CHOICES = [
        ('muscle_gain', 'Muscle Gain'),
        ('fat_loss', 'Fat Loss'),
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('general', 'General Fitness'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    target_muscles = models.JSONField(default=list)  # e.g., ["Chest", "Triceps"]
    goal_type = models.CharField(max_length=20, choices=GOAL_CHOICES)
    duration_minutes = models.PositiveIntegerField(default=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.difficulty})"


class WorkoutExercise(models.Model):
    """Exercises within a workout"""
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=200)
    sets = models.PositiveIntegerField()
    reps = models.CharField(max_length=50)  # e.g., "8-12", "30 sec"
    is_warmup = models.BooleanField(default=False)
    rest_time_seconds = models.PositiveIntegerField(default=60)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.workout.name})"


class Achievement(models.Model):
    """Unlockable achievements"""
    CATEGORY_CHOICES = [
        ('consistency', 'Consistency / Attendance'),
        ('muscle', 'Muscle-Specific'),
        ('savage', 'Savage / Failure'),
        ('discipline', 'Discipline / Mindset'),
        ('fun', 'Fun / Flex'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10)  # Emoji or icon class
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='fun')
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomerAchievement(models.Model):
    """Track unlocked achievements for members"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['member', 'achievement']
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.member.name} - {self.achievement.name}"


class WorkoutLog(models.Model):
    """Track completed workout sessions"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='workout_logs')
    workout = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.member.name} - {self.workout.name if self.workout else 'Deleted Workout'} - {self.completed_at}"
