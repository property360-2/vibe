"""
Seed data command for creating default membership plans and sample data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from core.models import MembershipPlan, Member, MembershipPass, Attendance


class Command(BaseCommand):
    help = 'Seed the database with default membership plans and sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-samples',
            action='store_true',
            help='Include sample members, passes, and attendance records',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')
        
        # Create default membership plans
        self.create_default_plans()
        
        # Optionally create sample data
        if options['with_samples']:
            self.create_sample_members()
            self.create_sample_passes()
            self.create_sample_attendance()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))

    def create_default_plans(self):
        """Create default membership plans"""
        plans = [
            {'name': '1-Day Pass', 'duration_days': 1, 'price': Decimal('60.00')},
            {'name': '3-Day Pass', 'duration_days': 3, 'price': Decimal('150.00')},
            {'name': '7-Day Pass', 'duration_days': 7, 'price': Decimal('250.00')},
        ]
        
        for plan_data in plans:
            plan, created = MembershipPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'duration_days': plan_data['duration_days'],
                    'price': plan_data['price'],
                    'is_active': True
                }
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  {status}: {plan.name} - ₱{plan.price}')

    def create_sample_members(self):
        """Create sample members"""
        sample_names = [
            ('Juan Dela Cruz', '09171234567'),
            ('Maria Santos', '09181234567'),
            ('Pedro Reyes', '09191234567'),
            ('Ana Garcia', '09201234567'),
            ('Jose Mendoza', '09211234567'),
            ('Rosa Aquino', '09221234567'),
            ('Carlos Ramos', '09231234567'),
            ('Elena Torres', '09241234567'),
            ('Miguel Cruz', '09251234567'),
            ('Sofia Bautista', None),
        ]
        
        self.stdout.write('\nCreating sample members...')
        for name, phone in sample_names:
            member, created = Member.objects.get_or_create(
                name=name,
                defaults={'phone': phone}
            )
            if created:
                self.stdout.write(f'  Created: {member.name}')

    def create_sample_passes(self):
        """Create sample passes for members"""
        self.stdout.write('\nCreating sample passes...')
        
        members = Member.objects.all()
        plans = list(MembershipPlan.objects.filter(is_active=True))
        
        if not plans:
            self.stdout.write('  No active plans found. Run without --with-samples first.')
            return
        
        today = timezone.now().date()
        
        for i, member in enumerate(members):
            # Skip if member already has passes
            if member.passes.exists():
                continue
            
            # Give some members active passes, some expired
            plan = random.choice(plans)
            
            if i % 3 == 0:  # Some expired passes
                start_date = today - timedelta(days=plan.duration_days + random.randint(1, 10))
                status = 'expired'
            else:  # Active passes
                start_date = today - timedelta(days=random.randint(0, plan.duration_days - 1))
                status = 'active'
            
            end_date = start_date + timedelta(days=plan.duration_days - 1)
            
            MembershipPass.objects.create(
                member=member,
                membership_plan=plan,
                start_date=start_date,
                end_date=end_date,
                price_snapshot=plan.price,
                status=status
            )
            self.stdout.write(f'  Created pass for {member.name}: {plan.name} ({status})')

    def create_sample_attendance(self):
        """Create sample attendance records"""
        self.stdout.write('\nCreating sample attendance...')
        
        # Get members with active passes
        today = timezone.now().date()
        active_passes = MembershipPass.objects.filter(
            status='active',
            end_date__gte=today
        )
        
        for membership_pass in active_passes:
            # Random number of check-ins in the past week
            num_checkins = random.randint(0, 5)
            
            for _ in range(num_checkins):
                # Random time in the past 7 days
                days_ago = random.randint(0, 6)
                hour = random.choice([6, 7, 8, 9, 17, 18, 19, 20])  # Common gym hours
                minute = random.randint(0, 59)
                
                checkin_time = timezone.now() - timedelta(
                    days=days_ago,
                    hours=timezone.now().hour - hour,
                    minutes=timezone.now().minute - minute
                )
                
                Attendance.objects.create(
                    member=membership_pass.member,
                    membership_pass=membership_pass,
                    checked_in_at=checkin_time
                )
            
            if num_checkins > 0:
                self.stdout.write(f'  Created {num_checkins} check-ins for {membership_pass.member.name}')
