from django.test import RequestFactory
from django.contrib.auth.models import User
from core.views import workout_library
from core.models import Workout

from core.models import Member

# Get a valid member
member = Member.objects.first()
if not member:
    print("No Member found! Creating a temp one for admin...")
    # fallback logic if strictly needed, but let's see if one exists first
    user = User.objects.first()
else:
    user = member.user
    print(f"Using user: {user.username} (Member ID: {member.id})")

if not user:
     print("No user available.")
else:
    # Setup request
    factory = RequestFactory()
    request = factory.get('/my-workouts/')
    request.user = user
    request.GET = {}

    # Add messages middleware mock
    from django.contrib.messages.storage.fallback import FallbackStorage
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    # Execute view
    try:
        response = workout_library(request)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code != 200:
             print(f"Response Location (if 302): {response.get('Location', 'N/A')}")
        
        content = response.content.decode('utf-8')
        
        print("\n--- DATA CHECKS ---")
        print(f"DB Active Workouts: {Workout.objects.filter(is_active=True).count()}")
        
        print("\n--- RENDER CHECKS ---")
        if "card-title" in content:
            print("SUCCESS: Found 'card-title' in HTML.")
            count = content.count("card-title")
            print(f"Count of cards found: {count}")
        else:
            print("FAILURE: No 'card-title' found in HTML.")
            
        if "No workouts found" in content:
            print("WARNING: 'No workouts found' message is present.")
            
        if "alert-danger" in content:
             print("SUCCESS: Found debug alert.")
        else:
             print("FAILURE: Did not find debug alert.")

        print("\n--- CONTENT SNIPPET ---")
        # Find where the card loop starts
        start_idx = content.find('class="card')
        if start_idx != -1:
            print(content[start_idx:start_idx+500])
        else:
            print("No card class found.")
            
    except Exception as e:
        print(f"Error executing view: {e}")
        import traceback
        traceback.print_exc()
