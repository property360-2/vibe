import os
import django
from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth.models import User
from core.models import Workout, Member

# Setup request
factory = RequestFactory()
request = factory.get('/my-workouts/')
user = User.objects.first()
request.user = user

# Setup context
member = getattr(user, 'member', None)
profile = getattr(member, 'profile', None)
workouts = Workout.objects.filter(is_active=True).order_by('-created_at')

# Pagination simulation
from django.core.paginator import Paginator
paginator = Paginator(workouts, 9)
page_obj = paginator.get_page(1)

context = {
    'member': member,
    'profile': profile,
    'recommended': [],
    'workouts': page_obj,
    'active_filters': [],
    'query': '',
    'current_difficulty': None,
    'current_goal': None,
    'page_title': 'My Workouts'
}

# Render
try:
    rendered = render_to_string('pages/workout_library.html', context, request=request)
    print("Render successful.")
    if "No workouts found" in rendered:
        print("FOUND: No workouts found message")
    else:
        print("NOT FOUND: No workouts found message")
        # Check if card titles exist
        if "card-title" in rendered:
            print("FOUND: card-title elements")
            # Print a snippet
            idx = rendered.find("card-title")
            print(rendered[idx:idx+100])
        else:
            print("NOT FOUND: card-title elements")
except Exception as e:
    print(f"Render failed: {e}")
