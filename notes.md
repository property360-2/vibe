Username
goku
Default Password
member123

# Customer UI Structure

The customer portal is designed to give members easy access to their gym activities and membership details. It is separated from the staff/admin views.

## 1. Global Navigation (Navbar)
*   **Links**:
    *   **My Dashboard**: The main landing page for members.
    *   **My Transactions**: A history of all membership plan purchases.
    *   **My Reports**: A detailed view of attendance history with date filtering.
*   **User Menu (Top Right)**:
    *   **Change Password**: Allows the member to update their login credentials.
    *   **Logout**: Securely ends the session.

## 2. My Dashboard (`/my-dashboard/`)
*   **Welcome Header**: Displays the member's name.
*   **Membership Status**:
    *   **Active**: Shows Plan Name, Days Remaining, and Expiration Date.
    *   **Inactive**: Shows a "No Active Plan" message.
*   **Recent Attendance**: A summary table of the most recent check-ins and check-outs.

## 3. My Transactions (`/my-transactions/`)
*   **Transaction History**: A full list of purchased plans.
    *   **Details**: Date Purchased, Plan Name, Duration, Validity Period, Price, and Status (Active/Expired).

## 4. My Reports (`/my-reports/`)
*   **Date Filter**: Allows members to search attendance records by specific date ranges.
*   **Attendance Table**: Detailed log including:
    *   **Date**: Date of visit.
    *   **Time In / Out**: Exact timestamps.
    *   **Duration**: How long the session lasted.
    *   **Status**: Checked In vs Completed.

## 5. Account Management
*   **Change Password**: A dedicated page for security updates.

---

# Smart Fitness Personalization

The Personalization feature uses member data to generate a tailored fitness roadmap. It can be accessed via the **User Menu (Profile Icon)** in the top right.

## 1. How it Works (Logic Flow)
1.  **Input Collection**: Members provide their Age, Gender (Male/Female), Experience Level (Beginner/Intermediate/Advanced), Training Frequency (1 to 6 days/week), and Primary Goal.
2.  **Profile Creation**: Data is stored in a `CustomerProfile` model, which acts as the "brain" for the member's fitness journey.
3.  **Dynamic Generation**: 
    - **Logic Engine (`FitnessService`)**: Processes inputs to generate a personalized experience without manual staff intervention.
    - **Weekly Structure**: Automatically selects a workout split based on training days:
        - *1 Day*: Full Body routine.
        - *2 Days*: Upper/Lower split.
        - *3 Days*: Full Body split.
        - *4 Days*: Upper/Lower split.
        - *5 Days*: PPL + Upper/Lower hybrid.
        - *6 Days*: PPL split.
    - **Objectives**: Sets a primary fitness goal and specific training bullet points (e.g., "Aim for progressive overload").
    - **BMI**: If Height/Weight are provided, it calculates BMI and assigns a health category.

## 2. Personalized Workouts
- The system filters the **Workout Library** to show "Recommended for You" routines.
- It matches workouts based on the member's **Experience Level** and **Primary Goal** (e.g., avoiding advanced powerlifting routines for beginners).

## 3. Manual Customization
- While the system provides a smart starting point, members have full control:
    - **Editable Structure**: Members can click "Edit" on their Weekly Structure to manually redefine muscle groups for specific days.
    - **Toggle Control**: Personalization can be disabled or enabled at any time to hide/show recommendations.

## 4. Achievements (Gamification)
- Provides psychological motivation by displaying available gym milestones like "Consistency King" or "Heavy Lifter". Currently, these are manually tracked milestones to encourage engagement.