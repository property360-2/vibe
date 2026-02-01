from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.db.models.functions import ExtractWeekDay, ExtractHour
from .models import Workout, Attendance

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
            },
            'conclusions': conclusions
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
