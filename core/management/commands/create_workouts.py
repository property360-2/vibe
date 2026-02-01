from django.core.management.base import BaseCommand
from core.models import Workout, WorkoutExercise, Achievement

class Command(BaseCommand):
    help = 'Populate database with initial workouts and achievements'

    def handle(self, *args, **kwargs):
        self.create_workouts()
        self.create_achievements()
        self.stdout.write(self.style.SUCCESS('Successfully populated database'))

    def create_workouts(self):
        standard_warmup = [
            ('Dynamic Stretching', 1, '5 mins', 0, True),
            ('Light Cardio (Jumping Jacks)', 1, '2 mins', 0, True),
        ]

        workouts_data = [
            # Beginner Workouts
            {
                'name': 'Beginner Full Body A',
                'description': 'A complete body workout focusing on fundamental movements. Great for starting out.',
                'difficulty': 'beginner',
                'target_muscles': ['Chest', 'Legs', 'Back', 'Core'],
                'goal_type': 'general',
                'duration_minutes': 45,
                'exercises': standard_warmup + [
                    ('Bodyweight Squats', 3, '12-15 reps', 60, False),
                    ('Push Ups (or Knee Push Ups)', 3, '8-12 reps', 60, False),
                    ('Dumbbell Rows', 3, '12 reps each', 60, False),
                    ('Plank', 3, '30 seconds', 45, False),
                ]
            },
            {
                'name': 'Beginner Full Body B',
                'description': 'Alternative full body routine to mix things up.',
                'difficulty': 'beginner',
                'target_muscles': ['Shoulders', 'Legs', 'Arms'],
                'goal_type': 'general',
                'duration_minutes': 45,
                'exercises': standard_warmup + [
                    ('Lunges', 3, '10 reps each leg', 60, False),
                    ('Dumbbell Overhead Press', 3, '10-12 reps', 60, False),
                    ('Lat Pulldowns', 3, '12-15 reps', 60, False),
                    ('Mountain Climbers', 3, '30 seconds', 45, False),
                ]
            },
            # Intermediate Workouts
            {
                'name': 'Intermediate Upper Body Push',
                'description': 'Focus on chest, shoulders, and triceps.',
                'difficulty': 'intermediate',
                'target_muscles': ['Chest', 'Shoulders', 'Triceps'],
                'goal_type': 'muscle_gain',
                'duration_minutes': 60,
                'exercises': standard_warmup + [
                    ('Bench Press', 4, '8-10 reps', 90, False),
                    ('Overhead Press', 3, '8-12 reps', 90, False),
                    ('Incline Dumbbell Press', 3, '10-12 reps', 90, False),
                    ('Lateral Raises', 3, '12-15 reps', 60, False),
                    ('Tricep Pushdowns', 3, '12-15 reps', 60, False),
                ]
            },
            {
                'name': 'Intermediate Upper Body Pull',
                'description': 'Focus on back and biceps.',
                'difficulty': 'intermediate',
                'target_muscles': ['Back', 'Biceps'],
                'goal_type': 'muscle_gain',
                'duration_minutes': 60,
                'exercises': standard_warmup + [
                    ('Pull Ups (or Assisted)', 4, 'AMRAP', 90, False),
                    ('Barbell Rows', 4, '8-10 reps', 90, False),
                    ('Face Pulls', 3, '12-15 reps', 60, False),
                    ('Bicep Curls', 3, '10-12 reps', 60, False),
                    ('Hammer Curls', 3, '10-12 reps', 60, False),
                ]
            },
            {
                'name': 'Intermediate Legs & Core',
                'description': 'Leg day essentials.',
                'difficulty': 'intermediate',
                'target_muscles': ['Legs', 'Core'],
                'goal_type': 'muscle_gain',
                'duration_minutes': 75,
                'exercises': standard_warmup + [
                    ('Barbell Squats', 4, '6-8 reps', 120, False),
                    ('Romanian Deadlifts', 3, '8-10 reps', 90, False),
                    ('Leg Press', 3, '10-12 reps', 90, False),
                    ('Calf Raises', 3, '15-20 reps', 60, False),
                    ('Hanging Leg Raises', 3, '10-15 reps', 60, False),
                ]
            },
            # Fat Loss / Cardio
            {
                'name': 'HIIT Cardio Blaster',
                'description': 'High intensity interval training to burn calories.',
                'difficulty': 'intermediate',
                'target_muscles': ['Full Body'],
                'goal_type': 'fat_loss',
                'duration_minutes': 30,
                'exercises': standard_warmup + [
                    ('Jumping Jacks', 4, '45 sec', 15, False),
                    ('Burpees', 4, '45 sec', 15, False),
                    ('High Knees', 4, '45 sec', 15, False),
                ]
            },
             # Advanced Workouts
            {
                'name': 'Advanced Chest Destruction',
                'description': 'High volume chest workout for experienced lifters.',
                'difficulty': 'advanced',
                'target_muscles': ['Chest'],
                'goal_type': 'muscle_gain',
                'duration_minutes': 90,
                'exercises': standard_warmup + [
                    ('Bench Press', 5, '5 reps', 180, False),
                    ('Incline Dumbbell Press', 4, '8-10 reps', 90, False),
                    ('Weighted Dips', 3, '10-12 reps', 90, False),
                    ('Cable Flyes', 3, '15-20 reps', 60, False),
                    ('Push Ups', 2, 'Failure', 60, False),
                ]
            },
             {
                'name': 'Advanced Back Builder',
                'description': 'Wide and thick back focus.',
                'difficulty': 'advanced',
                'target_muscles': ['Back'],
                'goal_type': 'muscle_gain',
                'duration_minutes': 90,
                'exercises': standard_warmup + [
                    ('Deadlifts', 4, '5 reps', 180, False),
                    ('Pull Ups', 4, '10 reps (weighted if needed)', 120, False),
                    ('T-Bar Rows', 3, '8-10 reps', 90, False),
                    ('Single Arm Dumbbell Rows', 3, '10-12 reps', 90, False),
                    ('Straight Arm Pulldowns', 2, '15 reps', 60, False),
                ]
            },
        ]

        created_count = 0
        updated_count = 0
        for data in workouts_data:
            workout, created = Workout.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'difficulty': data['difficulty'],
                    'target_muscles': data['target_muscles'],
                    'goal_type': data['goal_type'],
                    'duration_minutes': data['duration_minutes']
                }
            )
            
            if not created:
                # Update duration for existing
                workout.duration_minutes = data['duration_minutes']
                workout.save()
                # Clear existing exercises to rebuild with new fields
                workout.exercises.all().delete()
                updated_count += 1
            else:
                created_count += 1
                
            for idx, (ex_name, ex_sets, ex_reps, ex_rest, ex_warmup) in enumerate(data['exercises']):
                WorkoutExercise.objects.create(
                    workout=workout,
                    name=ex_name,
                    sets=ex_sets,
                    reps=ex_reps,
                    rest_time_seconds=ex_rest,
                    is_warmup=ex_warmup,
                    order=idx + 1
                )
                
        self.stdout.write(f'Created {created_count}, Updated {updated_count} workouts')

    def create_achievements(self):
        achievements_data = [
            # Consistency / Attendance
            ('Certified Masarap 😤🍗', 'Consistent gym attendance for 365 days. Discipline = attractive.', '😤', 'consistency', False),
            ('Di Ka Na Mamatay 🧟‍♂️', '180 days of continuous workouts. Hindi ka na pang soft.', '🧟‍♂️', 'consistency', False),
            ('Hindi Na Baguhan 🏃‍♂️', '30 total gym visits completed.', '🏃‍♂️', 'consistency', False),
            ('Pumasok Kahit Tinamad 😮‍💨', 'Logged a workout on a day with <30 min duration.', '😮‍💨', 'consistency', False),
            
            # Muscle-Specific
            ('Cobra 🐍', 'Completed 100+ back-focused workouts.', '🐍', 'muscle', False),
            ('Manok Legs No More 🐔➡️🦵', '50 leg day workouts completed.', '🦵', 'muscle', False),
            ('Tibay ng Dibdib 🦍', '75 chest workouts completed.', '🦍', 'muscle', False),
            ('Balikat ng Diyos 🗿', '60 shoulder-focused workouts completed.', '🗿', 'muscle', False),
            ('Bisig ni Tanggol 💪', '80 arm workouts completed.', '💪', 'muscle', False),
            
            # Savage / Failure (Hidden)
            ('Weakshit 🥲', 'Shame Badge: No gym activity for 30 consecutive days.', '🥲', 'savage', True),
            ('Ghost Member 👻', 'Brutal: Membership active but zero attendance.', '👻', 'savage', True),
            ('Nag Simula Pero Di Tinapos 🚶‍♂️', 'Reality Check: Stopped working out within 7 days of first visit.', '🚶‍♂️', 'savage', True),
            ('Failure ❌', 'Savage Legendary: Personalization enabled but no workout done for 60 days.', '❌', 'savage', True),
            
            # Discipline / Mindset
            ('No Excuses 🔥', 'Worked out during rainy days / holidays.', '🔥', 'discipline', False),
            ('Consistency > Motivation 🧠', '3 months of steady attendance (any pace).', '🧠', 'discipline', False),
            ('Gym Is Therapy 🖤', '100 total workouts completed.', '🖤', 'discipline', False),
            
            # Fun / Flex
            ('Picture muna bago umuwi 📸', 'Profile picture updated after gym visit.', '📸', 'fun', False),
            ('NPC No More 🎮', 'Switched from Beginner → Intermediate workouts.', '🎮', 'fun', False),
            ('Main Character Arc 🌅', 'Hit any long-term achievement (180+ days).', '🌅', 'fun', False),
        ]
        
        created_count = 0
        updated_count = 0
        for name, desc, icon, cat, hidden in achievements_data:
            obj, created = Achievement.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'icon': icon,
                    'category': cat,
                    'is_hidden': hidden
                }
            )
            if not created:
                obj.description = desc
                obj.icon = icon
                obj.category = cat
                obj.is_hidden = hidden
                obj.save()
                updated_count += 1
            else:
                created_count += 1
                
        self.stdout.write(f'Created {created_count}, Updated {updated_count} achievements')
