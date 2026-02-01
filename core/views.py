from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.paginator import Paginator
import random
import json

from .models import MembershipPlan, Member, MembershipPass, Attendance, CustomerProfile, Workout, Achievement, CustomerAchievement
from .forms import MembershipPlanForm, MemberForm, SellPassForm, CheckInForm
from . import services


@login_required
def dashboard(request):
    """Main dashboard with KPIs and insights"""
    # Redirect members to customer dashboard
    if hasattr(request.user, 'member'):
        return redirect('customer_dashboard')
        
    today_checkins = services.get_today_checkins()
    active_passes = services.get_active_passes_count()
    expired_passes = services.get_expired_passes_count()
    revenue_today = services.get_revenue_today()
    
    peak_hour, peak_count = services.get_peak_hour()
    peak_time = services.format_peak_hour(peak_hour)
    
    expected_data = services.get_expected_returns_next_3_days()
    ai_insights = services.generate_dashboard_insights()
    
    context = {
        'today_checkins': today_checkins,
        'active_passes': active_passes,
        'expired_passes': expired_passes,
        'revenue_today': revenue_today,
        'peak_time': peak_time,
        'peak_count': peak_count,
        'expected_returns': expected_data['expected_returns'],
        'high_churn_count': services.get_high_churn_count(),
        'ai_insights': ai_insights,
        'page_title': 'Dashboard',
    }
    return render(request, 'pages/dashboard.html', context)


# =============================================================================
# MEMBERSHIP PLANS
# =============================================================================

@login_required
def plans_list(request):
    """List and manage membership plans"""
    plans = MembershipPlan.objects.all()
    form = MembershipPlanForm()
    
    if request.method == 'POST':
        if 'create' in request.POST:
            form = MembershipPlanForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Plan created successfully!')
                return redirect('plans_list')
    
    context = {
        'plans': plans,
        'form': form,
        'page_title': 'Membership Plans',
    }
    return render(request, 'pages/plans.html', context)


@login_required
def plan_edit(request, pk):
    """Edit a membership plan"""
    plan = get_object_or_404(MembershipPlan, pk=pk)
    
    if request.method == 'POST':
        form = MembershipPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan updated successfully!')
            return redirect('plans_list')
    else:
        form = MembershipPlanForm(instance=plan)
    
    context = {
        'plan': plan,
        'form': form,
        'page_title': f'Edit Plan: {plan.name}',
    }
    return render(request, 'pages/plan_edit.html', context)


@login_required
def plan_delete(request, pk):
    """Delete a membership plan"""
    plan = get_object_or_404(MembershipPlan, pk=pk)
    
    if request.method == 'POST':
        try:
            plan.delete()
            messages.success(request, 'Plan deleted successfully!')
        except Exception as e:
            messages.error(request, f'Cannot delete plan: {str(e)}')
        return redirect('plans_list')
    
    context = {
        'plan': plan,
        'page_title': f'Delete Plan: {plan.name}',
    }
    return render(request, 'pages/plan_delete.html', context)


# =============================================================================
# MEMBERS
# =============================================================================

@login_required
def check_duplicate_member(request):
    """Check for duplicate member name via AJAX"""
    name = request.GET.get('name', '').strip()
    if not name:
        return JsonResponse({'status': 'ok'})
    
    # Case-insensitive check, exclude current member if editing (optional, skipping for now as per ID usually not passed here easily without logic)
    exists = Member.objects.filter(name__iexact=name).exists()
    
    if exists:
        return JsonResponse({'status': 'duplicate', 'message': 'A member with this name already exists.'})
    return JsonResponse({'status': 'ok'})

@login_required
def members_list(request):
    """List and search members"""
    query = request.GET.get('q', '')
    members = Member.objects.all()
    
    if query:
        members = members.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )
    
    # Handle AJAX search
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        data = []
        for member in members[:50]: # Limit results for performance
            status = 'Active' if member.has_active_pass() else 'No Pass'
            data.append({
                'pk': member.pk,
                'name': member.name,
                'initial': member.name[0].upper(),
                'phone': member.phone or 'No phone',
                'status': status,
                'joined': member.created_at.strftime('%b %d, %Y'),
                'has_active_pass': member.has_active_pass()
            })
        return JsonResponse({'status': 'success', 'data': data})

    form = MemberForm()
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if is_ajax:
            import json as py_json
            data = py_json.loads(request.body)
            form = MemberForm(data)
        else:
            form = MemberForm(request.POST)

        if form.is_valid():
            member = form.save(commit=False)
            
            # Create User account
            username = slugify(member.name).replace('-', '_')
            if User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(1000, 9999)}"
            
            user = User.objects.create_user(username=username, password='member123')
            member.user = user
            member.save()
            
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Member added successfully!',
                    'data': {
                        'name': member.name,
                        'phone': member.phone or 'No phone',
                        'pk': member.pk,
                        'joined': member.created_at.strftime('%b d, Y'),
                        'initial': member.name[0].upper(),
                        'username': user.username,
                        'password': 'member123'
                    }
                })
            
            messages.success(request, 'Member added successfully!')
            return redirect('members_list')
        
        if is_ajax:
            return JsonResponse({'status': 'error', 'error': form.errors.as_text()}, status=400)
    
    context = {
        'members': members,
        'plans': MembershipPlan.objects.filter(is_active=True),  # Pass active plans
        'form': form,
        'query': query,
        'page_title': 'Members',
    }
    return render(request, 'pages/members.html', context)


@login_required
def sell_pass(request):
    """API endpoint to sell a pass to a member"""
    if request.method == 'POST':
        import json as py_json
        try:
            data = py_json.loads(request.body)
            member_id = data.get('member_id')
            plan_id = data.get('plan_id')
            
            member = get_object_or_404(Member, pk=member_id)
            plan = get_object_or_404(MembershipPlan, pk=plan_id)
            
            # Check for active pass
            if member.has_active_pass():
                return JsonResponse({'status': 'error', 'error': 'Member already has an active pass.'}, status=400)
            
            # Create pass
            MembershipPass.objects.create(
                member=member,
                membership_plan=plan,
                start_date=timezone.now().date(),
                price_snapshot=plan.price
            )
            
            return JsonResponse({'status': 'success', 'message': f'Pass sold to {member.name}!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)



@login_required
def member_detail(request, pk):
    """Member detail with history and churn prediction"""
    member = get_object_or_404(Member, pk=pk)
    
    # Get pass history
    passes = member.passes.all()
    
    # Get attendance history
    attendances = member.attendances.all()[:20]
    
    # Get churn prediction and insights
    member_insights = services.generate_member_insights(member)
    
    context = {
        'member': member,
        'passes': passes,
        'attendances': attendances,
        'insights': member_insights,
        'page_title': f'Member: {member.name}',
    }
    return render(request, 'pages/member_detail.html', context)


@login_required
def member_edit(request, pk):
    """Edit a member"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member updated successfully!')
            return redirect('member_detail', pk=pk)
    else:
        form = MemberForm(instance=member)
    
    context = {
        'member': member,
        'form': form,
        'page_title': f'Edit Member: {member.name}',
    }
    return render(request, 'pages/member_edit.html', context)


@login_required
def member_delete(request, pk):
    """Delete a member"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Member deleted successfully!')
        return redirect('members_list')
    
    context = {
        'member': member,
        'page_title': f'Delete Member: {member.name}',
    }
    return render(request, 'pages/member_delete.html', context)


# =============================================================================
# PASSES
# =============================================================================

@login_required
def passes_list(request):
    """List passes and sell new ones"""
    today = timezone.now().date()
    
    # Update expired passes
    MembershipPass.objects.filter(
        end_date__lt=today,
        status='active'
    ).update(status='expired')
    
    active_passes = MembershipPass.objects.filter(status='active', end_date__gte=today)
    expired_passes = MembershipPass.objects.filter(status='expired')[:50]
    
    form = SellPassForm()
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if is_ajax:
            import json as py_json
            data = py_json.loads(request.body)
            form = SellPassForm(data)
        else:
            form = SellPassForm(request.POST)

        if form.is_valid():
            member = form.cleaned_data['member']
            plan = form.cleaned_data['membership_plan']
            
            # Create the pass
            new_pass = MembershipPass.objects.create(
                member=member,
                membership_plan=plan,
                start_date=today,
                price_snapshot=plan.price
            )
            
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'status': 'success',
                    'message': f'Pass sold to {member.name}!',
                    'data': {
                        'member_name': member.name,
                        'plan_name': plan.name,
                        'start_date': new_pass.start_date.strftime('%b %d'),
                        'end_date': new_pass.end_date.strftime('%b %d'),
                        'price': str(new_pass.price_snapshot),
                        'member_pk': member.pk
                    }
                })
            
            messages.success(request, f'Pass sold to {member.name}!')
            return redirect('passes_list')
        
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'error': form.errors.as_text()}, status=400)
    
    context = {
        'active_passes': active_passes,
        'expired_passes': expired_passes,
        'form': form,
        'page_title': 'Passes',
    }
    return render(request, 'pages/passes.html', context)


# =============================================================================
# ATTENDANCE
# =============================================================================

@login_required
def attendance_list(request):
    """Today's attendance and check-in"""
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(checked_in_at__date=today)
    
    form = CheckInForm()
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if is_ajax:
            import json as py_json
            data = py_json.loads(request.body)
            form = CheckInForm(data)
        else:
            form = CheckInForm(request.POST)

        if form.is_valid():
            member = form.cleaned_data['member']
            active_pass = member.get_active_pass()
            
            if active_pass:
                attendance = Attendance.objects.create(
                    member=member,
                    membership_pass=active_pass
                )
                
                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({
                        'status': 'success',
                        'message': f'{member.name} checked in successfully!',
                        'data': {
                            'member_name': member.name,
                            'plan_name': active_pass.membership_plan.name,
                            'checkin_time': attendance.checked_in_at.strftime('%I:%M %p'),
                            'member_pk': member.pk
                        }
                    })
                
                messages.success(request, f'{member.name} checked in successfully!')
                return redirect('attendance_list')
            
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'status': 'error', 'error': 'No active pass found.'}, status=400)
        
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'error': form.errors.as_text()}, status=400)
    
    context = {
        'attendances': today_attendance,
        'form': form,
        'today': today,
        'page_title': 'Attendance',
    }
    return render(request, 'pages/attendance.html', context)


# =============================================================================
# REPORTS
# =============================================================================

@login_required
def reports(request):
    """Analytics and reports page with tabs for transactions"""
    
    # Check if this is an AJAX request for sorting
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    if is_ajax:
        sort_by = request.GET.get('sort_by', '-date')
        tab = request.GET.get('tab', 'attendance')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        search = request.GET.get('search', '').strip()
        
        data = []
        if tab == 'attendance':
            # Mapping sort keys to model fields
            order_map = {
                'date': 'checked_in_at',
                '-date': '-checked_in_at',
                'member': 'member__name',
                '-member': '-member__name',
                'status': 'checked_out_at',
                '-status': '-checked_out_at'
            }
            ordering = order_map.get(sort_by, '-checked_in_at')
            queryset = Attendance.objects.select_related('member', 'membership_pass__membership_plan').all()
            
            # Filtering
            if start_date:
                queryset = queryset.filter(checked_in_at__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(checked_in_at__date__lte=end_date)
            if search:
                queryset = queryset.filter(member__name__icontains=search)
                
            queryset = queryset.order_by(ordering)[:100] # Increased limit/pagination might be needed later
            
            for item in queryset:
                status = 'Active' if item.checked_out_at is None else 'Completed'
                data.append({
                    'date': item.checked_in_at.strftime('%b %d, %Y'),
                    'time_in': item.checked_in_at.strftime('%I:%M %p'),
                    'time_out': item.checked_out_at.strftime('%I:%M %p') if item.checked_out_at else '-',
                    'member': item.member.name,
                    'status': status,
                    'plan': item.membership_pass.membership_plan.name
                })
                
        elif tab == 'passes':
            order_map = {
                'date': 'start_date',
                '-date': '-start_date',
                'member': 'member__name',
                '-member': '-member__name',
                'plan': 'membership_plan__name',
                '-plan': '-membership_plan__name',
                'price': 'price_snapshot',
                '-price': '-price_snapshot'
            }
            ordering = order_map.get(sort_by, '-start_date')
            queryset = MembershipPass.objects.select_related('member', 'membership_plan').all()
            
            # Filtering
            if start_date:
                queryset = queryset.filter(start_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(start_date__lte=end_date)
            if search:
                from django.db.models import Q
                queryset = queryset.filter(Q(member__name__icontains=search) | Q(membership_plan__name__icontains=search))
                
            queryset = queryset.order_by(ordering)[:100]
            
            for item in queryset:
                data.append({
                    'date': item.start_date.strftime('%b %d, %Y'),
                    'member': item.member.name,
                    'plan': item.membership_plan.name,
                    'price': str(item.price_snapshot),
                    'status': item.status.title()
                })

        
        return JsonResponse({'status': 'success', 'data': data})

    # Standard Page Load
    sales_by_plan = list(services.get_sales_count_by_plan())
    revenue_by_plan = list(services.get_revenue_by_plan())
    popular_plan = services.get_most_popular_plan()
    churn_distribution = services.get_churn_distribution()
    hourly_distribution = services.get_hourly_distribution()
    total_revenue = services.get_total_revenue()
    
    # Recent Transactions for Initial Load
    recent_attendance = Attendance.objects.select_related('member').order_by('-checked_in_at')[:20]
    recent_passes = MembershipPass.objects.select_related('member', 'membership_plan').order_by('-start_date')[:20]
    
    context = {
        'sales_by_plan': sales_by_plan,
        'revenue_by_plan': revenue_by_plan,
        'popular_plan': popular_plan,
        'churn_distribution': churn_distribution,
        'hourly_distribution': json.dumps(hourly_distribution),
        'total_revenue': total_revenue,
        'recent_attendance': recent_attendance,
        'recent_passes': recent_passes,
        'page_title': 'Reports',
    }
    return render(request, 'pages/reports.html', context)


@login_required
def check_in_member(request, pk):
    """Check in a member"""
    member = get_object_or_404(Member, pk=pk)
    active_pass = member.get_active_pass()
    
    if not active_pass:
        messages.error(request, f'{member.name} does not have an active pass.')
        return redirect('members_list')
    
    # Check if already checked in today without checkout
    today = timezone.now().date()
    existing = Attendance.objects.filter(
        member=member,
        checked_in_at__date=today,
        checked_out_at__isnull=True
    ).exists()
    
    if existing:
        messages.warning(request, f'{member.name} is already checked in.')
    else:
        Attendance.objects.create(member=member, membership_pass=active_pass)
        messages.success(request, f'{member.name} checked in successfully!')
        
    return redirect('members_list')


@login_required
def check_out_member(request, pk):
    """Check out a member"""
    member = get_object_or_404(Member, pk=pk)
    today = timezone.now().date()
    
    attendance = Attendance.objects.filter(
        member=member,
        checked_in_at__date=today,
        checked_out_at__isnull=True
    ).last()
    
    if attendance:
        attendance.checked_out_at = timezone.now()
        attendance.save()
        messages.success(request, f'{member.name} checked out successfully!')
    else:
        messages.error(request, f'{member.name} is not checked in.')
        
    return redirect('members_list')


@login_required
def customer_dashboard(request):
    """Dashboard for logged-in customers"""
    try:
        member = request.user.member
    except (AttributeError, Member.DoesNotExist):
        messages.error(request, "You are not a member.")
        return redirect('dashboard')
        
    active_pass = member.get_active_pass()
    days_left = active_pass.days_remaining if active_pass else 0
    
    attendances = member.attendances.all()[:10]
    
    # ML Insights
    prob, risk_level = services.predict_churn(member)
    
    context = {
        'member': member,
        'active_pass': active_pass,
        'days_left': days_left,
        'attendances': attendances,
        'return_prob': int(prob * 100),
        'risk_level': risk_level,
        'page_title': 'My Dashboard',
    }
    return render(request, 'pages/customer_dashboard.html', context)


@login_required
def customer_transactions(request):
    """Transactions history for logged-in customers with async support"""
    try:
        member = request.user.member
    except (AttributeError, Member.DoesNotExist):
        messages.error(request, "You are not a member.")
        return redirect('dashboard')
        
    transactions = member.passes.select_related('membership_plan').all()
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter in ['active', 'expired']:
        transactions = transactions.filter(status=status_filter)
        
    date_filter = request.GET.get('date_range')
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    if date_filter == 'this_month':
        transactions = transactions.filter(created_at__month=now.month, created_at__year=now.year)
    elif date_filter == 'last_3_months':
        three_months_ago = now - timedelta(days=90)
        transactions = transactions.filter(created_at__gte=three_months_ago)
    elif date_filter == 'this_year':
        transactions = transactions.filter(created_at__year=now.year)
        
    # Sorting
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = ['created_at', '-created_at', 'price_snapshot', '-price_snapshot']
    if sort in valid_sorts:
        transactions = transactions.order_by(sort)
    else:
        transactions = transactions.order_by('-created_at')

    context = {
        'member': member,
        'transactions': transactions,
        'page_title': 'My Transactions',
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/transaction_rows.html', context)
        
    return render(request, 'pages/customer_transactions.html', context)


@login_required
def customer_reports(request):
    """Attendance reports for logged-in customers"""
    try:
        member = request.user.member
    except (AttributeError, Member.DoesNotExist):
        messages.error(request, "You are not a member.")
        return redirect('dashboard')
        
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    attendances = member.attendances.all().order_by('-checked_in_at')
    
    if start_date:
        attendances = attendances.filter(checked_in_at__date__gte=start_date)
    if end_date:
        attendances = attendances.filter(checked_in_at__date__lte=end_date)
        
    fitness_service = services.FitnessService()
    analytics = fitness_service.get_member_analytics(member)
        
    context = {
        'member': member,
        'attendances': attendances,
        'analytics': analytics,
        'page_title': 'My Reports',
    }
    return render(request, 'pages/customer_reports.html', context)


@login_required
def change_password(request):
    """Allow members to change their password"""
    if request.method == 'POST':
        from django.contrib.auth.forms import PasswordChangeForm
        from django.contrib.auth import update_session_auth_hash
        
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('customer_dashboard')
    else:
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user)
    
    return render(request, 'pages/change_password.html', {
        'form': form,
        'page_title': 'Change Password'
    })


@login_required
def customer_personalization(request):
    """Handle customer fitness personalization"""
    try:
        member = request.user.member
    except (AttributeError, Member.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    profile, created = CustomerProfile.objects.get_or_create(
        member=member,
        defaults={
            'age': 25,
            'experience': 'beginner',
            'training_days': 3,
            'primary_goal': 'general'
        }
    )
    
    fitness_service = services.FitnessService()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'disable':
            profile.is_active = False
            profile.save()
            messages.info(request, "Personalization disabled.")
        elif action == 'enable':
            profile.is_active = True
            profile.save()
            messages.success(request, "Personalization enabled!")
        elif action == 'update_structure':
            # Handle manual structure edits
            new_schedule = {}
            for day in range(1, profile.training_days + 1):
                day_content = request.POST.get(f'day_{day}')
                # Split by comma and clean up
                if day_content:
                    muscles = [m.strip() for m in day_content.split(',') if m.strip()]
                    new_schedule[str(day)] = muscles
            
            profile.weekly_schedule = new_schedule
            profile.save()
            messages.success(request, "Weekly structure updated!")
            
        else: # Update Profile Configuration
            old_days = profile.training_days
            
            profile.age = request.POST.get('age')
            profile.gender = request.POST.get('gender')
            profile.experience = request.POST.get('experience')
            profile.training_days = int(request.POST.get('training_days'))
            profile.primary_goal = request.POST.get('primary_goal')
            profile.savage_mode = request.POST.get('savage_mode') == 'on'
            profile.height_cm = request.POST.get('height_cm') or None
            profile.weight_kg = request.POST.get('weight_kg') or None
            

            profile.is_active = True
            
            # If training days changed, or if schedule is empty, regenerate it
            if old_days != profile.training_days or not profile.weekly_schedule:
                profile.weekly_schedule = fitness_service.generate_weekly_structure(profile)
                messages.warning(request, "Profile updated & schedule regenerated based on new settings.")
            else:
                 messages.success(request, "Profile configuration updated!")
                 
            profile.save()
        
        return redirect('customer_personalization')
        
    # Generate Output Data
    
    # Ensure schedule exists if active
    if profile.is_active and not profile.weekly_schedule:
        profile.weekly_schedule = fitness_service.generate_weekly_structure(profile)
        profile.save()
    
    bmi_data = fitness_service.calculate_bmi(profile.height_cm, profile.weight_kg)
    objectives = fitness_service.generate_objectives(profile) if profile.is_active else None
    
    # Achievements
    all_achievements = Achievement.objects.all()
    user_achievements = CustomerAchievement.objects.filter(member=member).values_list('achievement_id', flat=True)
    
    # Group achievements by category
    categories = Achievement.CATEGORY_CHOICES
    grouped_achievements = []
    
    for cat_slug, cat_name in categories:
        # Get achievements for this category
        cat_items = all_achievements.filter(category=cat_slug)
        
        # Filter hidden and savage mode
        visible_items = []
        for ach in cat_items:
            is_unlocked = ach.id in user_achievements
            
            if ach.category == 'savage':
                if profile.savage_mode or is_unlocked:
                    visible_items.append(ach)
            elif ach.is_hidden:
                if is_unlocked:
                    visible_items.append(ach)
            else:
                visible_items.append(ach)
        
        if visible_items:
            grouped_achievements.append({
                'slug': cat_slug,
                'name': cat_name,
                'items': visible_items
            })
    
    context = {
        'member': member,
        'profile': profile,
        'bmi_data': bmi_data,
        'weekly_structure': profile.weekly_schedule, 
        'objectives': objectives,
        'grouped_achievements': grouped_achievements,
        'user_achievements': user_achievements,
        'total_achievements': all_achievements.count(),
        'page_title': 'My Personalization',

    }
    return render(request, 'pages/customer_personalization.html', context)


@login_required
def workout_library(request):
    """Display workout library"""
    try:
        member = request.user.member
        profile = getattr(member, 'profile', None)
    except (AttributeError, Member.DoesNotExist):
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    fitness_service = services.FitnessService()
    
    # Recommended Workouts
    recommended = []
    if profile and profile.is_active:
        recommended = fitness_service.get_recommended_workouts(profile)
        
    # Filter Library
    workouts = Workout.objects.filter(is_active=True).order_by('-created_at')
    
    query = request.GET.get('q')
    difficulty = request.GET.get('difficulty')
    goal = request.GET.get('goal')
    
    active_filters = []
    
    if query:
        workouts = workouts.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(target_muscles__icontains=query)
        )
        active_filters.append({'label': f'Search: {query}', 'param': 'q'})
        
    if difficulty:
        workouts = workouts.filter(difficulty=difficulty)
        active_filters.append({'label': f'Difficulty: {difficulty.title()}', 'param': 'difficulty'})
        
    if goal:
        workouts = workouts.filter(goal_type=goal)
        active_filters.append({'label': f'Goal: {goal.replace("_", " ").title()}', 'param': 'goal'})
        
    # Pagination
    paginator = Paginator(workouts, 9) # 9 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'member': member,
        'profile': profile,
        'recommended': recommended,
        'workouts': page_obj,
        'active_filters': active_filters,
        'query': query,
        'current_difficulty': difficulty,
        'current_goal': goal,
        'page_title': 'My Workouts'
    }
    return render(request, 'pages/workout_library.html', context)


@login_required
def workout_detail(request, pk):
    """Display workout details"""
    workout = get_object_or_404(Workout, pk=pk)
    
    context = {
        'workout': workout,
        'page_title': workout.name
    }
    return render(request, 'pages/workout_detail.html', context)
