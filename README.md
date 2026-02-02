# Gym ng mga Super Saiyan

An open-source Gym Management System designed for efficiency and ease of use. This system allows you to manage memberships, track attendance, browse a comprehensive workout library, and earn achievements for your fitness progress.

## Author
**Jun Alvior**

## Open Source
This project is open-source! You are free to modification this system at will to suit your specific needs or to contribute back to its development.

## Technology Stack
The system is built with a modern and robust stack:
*   **Backend:** Django (Python 3.x)
*   **Database:** SQLite (default, easily portable)
*   **Frontend:** HTML5, Vanilla CSS, Bootstrap 5
*   **Icons:** Material Icons & Emojis
*   **State Management:** Built-in Django Session & Authentication

## How It Works
The system revolves around three core pillars: **Membership**, **Engagement**, and **Tracking**.

### 1. Membership Management
*   **Plans:** Admin can define custom plans (e.g., 1-Day, 7-Day, Monthly) with specific prices and durations.
*   **Passes:** Members purchase "Passes" tied to these plans. The system automatically calculates expiration dates.
*   **User Profiles:** Detailed member profiles including experience level (Beginner to Advanced), primary goals (Muscle Gain, Fat Loss, etc.), and physical stats (height/weight).

### 2. Attendance & Tracking
*   **Digital Check-in:** Members check in for their sessions, allowing the system to track usage frequency and active members.
*   **Workout Logs:** Users can log their completed workout sessions to track their fitness journey.

### 3. Engagement & Workouts
*   **Workout Library:** A collection of pre-defined workouts with detailed exercises, sets, reps, and difficulty levels.
*   **Savage Mode:** Users can toggle "Savage Mode" in their profiles for a more intense experience.

## Achievements
The system features a gamified achievement system to keep members motivated. Categories include:
*   **Consistency:** Awarded for regular attendance and long-term commitment.
*   **Muscle-Specific:** Earned for targeting specific muscle groups or completing specialized workout programs.
*   **Savage:** Special achievements for weakshits and not concistent
*   **Discipline:** Focused on mindset, routine, and sticking to the plan.
*   **Fun:** Lighthearted rewards for social engagement or unique milestones.

## Setup and Modification
To get started:
1.  Clone the repository.
2.  Install dependencies: `pip install django`
3.  Run migrations: `python manage.py migrate`
4.  Seed initial data (optional): `python manage.py seed_data --with-samples`
5.  Start the server: `python manage.py runserver`

Feel free to modify the templates or core logic to fit your gym's unique "Super Saiyan" vibe!
