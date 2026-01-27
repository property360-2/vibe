from django.db import models
from django.utils import timezone
from datetime import timedelta


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
    """Member check-in records"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendances')
    membership_pass = models.ForeignKey(MembershipPass, on_delete=models.CASCADE, related_name='attendances')
    checked_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_in_at']
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.member.name} - {self.checked_in_at.strftime('%Y-%m-%d %H:%M')}"
