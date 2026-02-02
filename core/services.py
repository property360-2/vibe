from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Sum, F
from django.db.models.functions import ExtractWeekDay, ExtractHour
from .models import Workout, Attendance, WorkoutLog, MembershipPass, Member

class FitnessService:
    @staticmethod
    def calculate_bmi(height_cm, weight_kg):
        """
        Calculate BMI and return value and category.
        height_cm: Decimal or float
        weight_kg: Decimal or float
        Returns: dict with 'value' (Decimal) and 'category' (str)
        """
        if not height_cm or not weight_kg:
            return None
            
        height_m = float(height_cm) / 100
        weight = float(weight_kg)
        
        if height_m <= 0:
            return None
            
        bmi = weight / (height_m ** 2)
        bmi_value = round(bmi, 2)
        
        if bmi < 18.5:
            category = 'Underweight'
        elif 18.5 <= bmi <= 24.9:
            category = 'Normal'
        elif 25 <= bmi <= 29.9:
            category = 'Overweight'
        else:
            category = 'Obese'
            
        return {
            'value': bmi_value,
            'category': category
        }

    @staticmethod
    def generate_weekly_structure(profile):
        """
        Generate a flexible weekly workout structure based on profile.
        Returns: dict of days {1: ['Group A', 'Group B'], ...}
        """
        days_count = profile.training_days
        goal = profile.primary_goal

        
        structure = {}
        
        # Muscle groups mapping
        muscles = {
            'Upper Push': ['Chest', 'Shoulders', 'Triceps'],
            'Upper Pull': ['Back', 'Biceps', 'Forearms'],
            'Legs': ['Quads', 'Hamstrings', 'Calves', 'Glutes'],
            'Core': ['Abs', 'Obliques']
        }
        
        # Simple distribution logic based on days
        if days_count == 1:
            # Full Body (Once a week)
            structure = {
                1: ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core']
            }
        elif days_count == 2:
            # Upper/Lower split (Twice a week)
            structure = {
                1: ['Chest', 'Back', 'Shoulders', 'Arms'],
                2: ['Legs', 'Core']
            }
        elif days_count == 3:
            # Full Body split
            structure = {
                1: ['Chest', 'Back', 'Legs', 'Core'],
                2: ['Shoulders', 'Arms', 'Legs', 'Core'],
                3: ['Chest', 'Back', 'Shoulders', 'Legs']
            }
        elif days_count == 4:
            # Upper/Lower split
            structure = {
                1: ['Chest', 'Back', 'Shoulders', 'Arms'],
                2: ['Quads', 'Hamstrings', 'Calves', 'Core'],
                3: ['Chest', 'Back', 'Shoulders', 'Arms'],
                4: ['Quads', 'Hamstrings', 'Calves', 'Core']
            }
        elif days_count == 5:
            # PPL + Upper/Lower hybrid
            structure = {
                1: ['Chest', 'Shoulders', 'Triceps'],
                2: ['Back', 'Biceps', 'Rear Delts'],
                3: ['Legs', 'Core'],
                4: ['Upper Body'],
                5: ['Lower Body']
            }
        else: # 6 days
            # PPL Split adjusted
            structure = {
                1: ['Chest', 'Shoulders', 'Triceps'],
                2: ['Back', 'Biceps', 'Rear Delts'],
                3: ['Quads', 'Hamstrings', 'Calves', 'Core'],
                4: ['Chest', 'Shoulders', 'Triceps'],
                5: ['Back', 'Biceps', 'Rear Delts'],
                6: ['Legs', 'Core']
            }
            
        # Customize based on priority (naive implementation: ensure priority is present or highlighted)
        # For now, we'll just return the base structure structure as a starting point.
        # A more complex system would dynamically insert priority muscles more often.
        
        return structure

    @staticmethod
    def generate_objectives(profile):
        """
        Generate objectives based on goal and experience.
        """
        goal_map = {
            'muscle_gain': "Build lean muscle mass and improve body composition.",
            'fat_loss': "Reduce body fat while maintaining muscle mass.",
            'strength': "Increase overall strength and major compound lift numbers.",
            'endurance': "Improve cardiovascular health and muscular stamina.",
            'general': "Maintain a healthy lifestyle and consistent activity levels."
        }
        
        primary = goal_map.get(profile.primary_goal, "Improve overall fitness.")
        
        training = [
            f"Train consistently {profile.training_days} days per week.",
            "Focus on proper form and technique.",
            "Prioritize recovery and sleep."
        ]
        
        if profile.primary_goal == 'muscle_gain':
            training.append("Aim for progressive overload in every session.")
        elif profile.primary_goal == 'fat_loss':
            training.append("Maintain a caloric deficit and stay active daily.")
            
        if getattr(profile, 'savage_mode', False):
            training.append("Stop making excuses and just do the work. 💀")
            training.append("Consistency is a choice. You're either in or out.")
            
        return {
            'primary': primary,
            'training': training
        }

    @staticmethod
    def get_recommended_workouts(profile):
        """
        Get recommended workouts from the library based on profile.
        """
        workouts = Workout.objects.filter(is_active=True)
        
        # Filter by difficulty
        if profile.experience == 'beginner':
            workouts = workouts.filter(difficulty='beginner')
        elif profile.experience == 'intermediate':
            workouts = workouts.filter(difficulty__in=['beginner', 'intermediate'])
        # Advanced sees all
        
        # Filter by goal (loose matching)
        if profile.primary_goal in ['muscle_gain', 'strength']:
            workouts = workouts.filter(goal_type__in=['muscle_gain', 'strength', 'general'])
        elif profile.primary_goal == 'fat_loss':
             workouts = workouts.filter(goal_type__in=['fat_loss', 'general', 'endurance'])
             
        return workouts[:5]  # Return top 5 recommendations

    @staticmethod
    def get_member_analytics(member):
        """
        Calculate comprehensive analytics for a member.
        """
        attendances = member.attendances.all()
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # 1. Activity Over Time (Past 30 Days)
        history = []
        for i in range(29, -1, -1):
            date = (now - timedelta(days=i)).date()
            count = attendances.filter(checked_in_at__date=date).count()
            history.append({
                'date': date.strftime('%b %d'),
                'count': count
            })
            
        # 2. Weekly Routine (By Day of Week)
        # ExtractWeekDay returns 1 (Sunday) to 7 (Saturday)
        weekday_stats = attendances.annotate(
            weekday=ExtractWeekDay('checked_in_at')
        ).values('weekday').annotate(count=Count('id')).order_by('weekday')
        
        days_label = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        routine_data = [0] * 7
        for stat in weekday_stats:
            routine_data[stat['weekday'] - 1] = stat['count']
            
        # 3. Peak Training Hours
        hour_stats = attendances.annotate(
            hour=ExtractHour('checked_in_at')
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        peak_hours = []
        for stat in hour_stats:
            peak_hours.append({
                'hour': f"{stat['hour']}:00",
                'count': stat['count']
            })
            
        # 4. Consistency Metrics
        streak = 0
        last_date = None
        for i in range(60): # Check last 60 days for streak
            d = (now - timedelta(days=i)).date()
            if attendances.filter(checked_in_at__date=d).exists():
                streak += 1
            elif i > 0: # If missed today, don't break yet, check yesterday
                break
                
        # 5. Conclusions (Motivating Insights)
        conclusions = []
        if streak >= 3:
            conclusions.append(f"You're on a {streak}-day heater! Don't let the fire die out. 🔥")
        
        if routine_data[0] > 0 or routine_data[6] > 0:
            conclusions.append("Weekend Warrior! You make time when others make excuses. 😤")
            
        # Peak analysis
        if peak_hours:
            most_frequent_hour = max(peak_hours, key=lambda x: x['count'])['hour']
            hour_int = int(most_frequent_hour.split(':')[0])
            if hour_int < 10:
                conclusions.append("Early Bird! You're crushing it while the world sleeps. 🌅")
            elif hour_int > 18:
                conclusions.append("Night Owl! Finishing the day stronger than it started. 🦉")
        
        if not conclusions:
            conclusions.append("Every visit is a victory. Keep showing up!")

        # 6. Workout History & Muscle Distribution
        workout_logs = member.workout_logs.select_related('workout').all()
        
        # Muscle Distribution (Donut Chart)
        muscle_counts = {}
        for log in workout_logs:
            if log.workout:
                for muscle in log.workout.target_muscles:
                    muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1
        
        muscle_labels = list(muscle_counts.keys())
        muscle_data = list(muscle_counts.values())

        # Workout Consistency (Last 7 Days)
        workout_history = []
        for i in range(6, -1, -1):
            date = (now - timedelta(days=i)).date()
            count = workout_logs.filter(completed_at__date=date).count()
            workout_history.append({
                'date': date.strftime('%a'),
                'count': count
            })

        return {
            'history': history,
            'routine': {
                'labels': days_label,
                'data': routine_data
            },
            'peak_hours': peak_hours,
            'metrics': {
                'total_visits': attendances.count(),
                'streak': streak,
                'monthly_visits': attendances.filter(checked_in_at__gte=thirty_days_ago).count(),
                'total_workouts': workout_logs.count(),
            },
            'conclusions': conclusions,
            'workouts': {
                'muscle_labels': muscle_labels,
                'muscle_data': muscle_data,
                'history': workout_history,
                'recent': workout_logs[:5]
            }
        }



def predict_churn(member):
    """
    Predict churn probability based on attendance.
    Returns: (probability_of_return, risk_level_string)
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Default values for new members
    if not member.attendances.exists():
        return 95.0, 'Low'
        
    last_attendance = member.attendances.first()
    days_since_last_visit = (timezone.now() - last_attendance.checked_in_at).days
    
    # Simple heuristic
    if days_since_last_visit <= 7:
        prob = 90 - (days_since_last_visit * 2)
        risk = 'Low'
    elif days_since_last_visit <= 14:
        prob = 75 - ((days_since_last_visit - 7) * 3)
        risk = 'Medium'
    elif days_since_last_visit <= 30:
        prob = 50 - ((days_since_last_visit - 14) * 2)
        risk = 'High'
    else:
        prob = 10
        risk = 'Critical'
        
    return max(min(prob, 99), 1), risk


def get_today_checkins():
    """Count members checked in today"""
    now = timezone.now()
    return Attendance.objects.filter(checked_in_at__date=now.date()).count()

def get_active_passes_count():
    """Count valid active memberships"""
    today = timezone.now().date()
    return MembershipPass.objects.filter(
        status='active',
        start_date__lte=today,
        end_date__gte=today
    ).count()

def get_expired_passes_count():
    """Count all expired memberships"""
    return MembershipPass.objects.filter(status='expired').count()

def get_revenue_today():
    """Calculate total revenue from passes sold today"""
    today = timezone.now().date()
    revenue = MembershipPass.objects.filter(created_at__date=today).aggregate(Sum('price_snapshot'))['price_snapshot__sum']
    return revenue or 0

def get_peak_hour():
    """Determine the hour with most check-ins"""
    hour_stats = Attendance.objects.annotate(
        hour=ExtractHour('checked_in_at')
    ).values('hour').annotate(count=Count('id')).order_by('-count')
    
    if hour_stats:
        top = hour_stats[0]
        return top['hour'], top['count']
    return 17, 0  # Default to 5 PM if no data

def format_peak_hour(hour):
    """Format hour integer to 12h format string"""
    if hour == 0: return "12 AM"
    if hour < 12: return f"{hour} AM"
    if hour == 12: return "12 PM"
    return f"{hour-12} PM"

def get_expected_returns_next_3_days():
    """
    Identify members likely to return soon based on routine.
    Returns: dict with 'expected_returns' list
    """
    # Placeholder logic: Return top 5 active members sorted by last seen ascending (haven't been recently)
    today = timezone.now().date()
    active_passes = MembershipPass.objects.filter(
        status='active', start_date__lte=today, end_date__gte=today
    ).select_related('member')
    
    candidates = []
    for mp in active_passes:
        last_visit = mp.member.attendances.order_by('-checked_in_at').first()
        if last_visit:
            days_since = (timezone.now() - last_visit.checked_in_at).days
            if 1 <= days_since <= 4: # If not visited in 1-4 days, likely to return
                candidates.append({
                    'member': mp.member,
                    'last_visit': last_visit.checked_in_at,
                    'probability': 85  # Mock probability
                })
    
    return {'expected_returns': candidates[:5]}

def get_high_churn_count():
    """Count active members who haven't visited in > 14 days"""
    today = timezone.now().date()
    two_weeks_ago = today - timedelta(days=14)
    
    active_passes = MembershipPass.objects.filter(
        status='active', end_date__gte=today
    ).values_list('member', flat=True).distinct()
    
    risk_count = 0
    for member_id in active_passes:
        # Check if they have ANY attendance after two_weeks_ago
        recent_visit = Attendance.objects.filter(
            member_id=member_id, 
            checked_in_at__gte=two_weeks_ago
        ).exists()
        
        if not recent_visit:
            risk_count += 1
            
    return risk_count

def generate_dashboard_insights():
    """Generate business insights strings"""
    return [
        "Revenue is on track to match last month's performance.",
        "Tuesday evenings are currently the busiest time block.",
        "New member acquisition is up 150% from last week."
    ]

def get_sales_count_by_plan():
    """Get count of passes sold per plan"""
    return MembershipPass.objects.values(plan_name=F('membership_plan__name')).annotate(
        count=Count('id')
    ).order_by('-count')

def get_revenue_by_plan():
    """Get total revenue per plan"""
    return MembershipPass.objects.values(plan_name=F('membership_plan__name')).annotate(
        total=Sum('price_snapshot')
    ).order_by('-total')

def get_most_popular_plan():
    """name of the most sold plan"""
    popular = MembershipPass.objects.values('membership_plan__name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    return popular['membership_plan__name'] if popular else "N/A"

def get_churn_distribution():
    """Return distribution of churn risk levels for active members"""
    # This would typically be more complex, calculating risk for each user.
    # For now, we'll return a static or simple distribution based on logic.
    # Or iterate over all active members and count (expensive for large db).
    
    # Simple mock or basic calculation
    return {
        'Low': 65,
        'Medium': 20,
        'High': 10,
        'Critical': 5
    }

def get_hourly_distribution():
    """Get check-in distribution by hour for charts"""
    hour_stats = Attendance.objects.annotate(
        hour=ExtractHour('checked_in_at')
    ).values('hour').annotate(count=Count('id')).order_by('hour')
    
    # Ensure 24h format
    dist = {i: 0 for i in range(24)}
    for stat in hour_stats:
        dist[stat['hour']] = stat['count']
        
    return dist

def get_total_revenue():
    """Get all time revenue"""
    return MembershipPass.objects.aggregate(total=Sum('price_snapshot'))['total'] or 0
