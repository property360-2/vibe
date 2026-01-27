from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
import json

from .models import MembershipPlan, Member, MembershipPass, Attendance
from .forms import MembershipPlanForm, MemberForm, SellPassForm, CheckInForm
from . import services


@login_required
def dashboard(request):
    """Main dashboard with KPIs and insights"""
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
def members_list(request):
    """List and search members"""
    query = request.GET.get('q', '')
    members = Member.objects.all()
    
    if query:
        members = members.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )
    
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
            member = form.save()
            
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'status': 'success',
                    'message': 'Member added successfully!',
                    'data': {
                        'name': member.name,
                        'phone': member.phone or 'No phone',
                        'pk': member.pk,
                        'joined': member.created_at.strftime('%b d, Y'),
                        'initial': member.name[0].upper()
                    }
                })
            
            messages.success(request, 'Member added successfully!')
            return redirect('members_list')
        
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'error': form.errors.as_text()}, status=400)
    
    context = {
        'members': members,
        'form': form,
        'query': query,
        'page_title': 'Members',
    }
    return render(request, 'pages/members.html', context)



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
    """Analytics and reports page"""
    sales_by_plan = list(services.get_sales_count_by_plan())
    revenue_by_plan = list(services.get_revenue_by_plan())
    popular_plan = services.get_most_popular_plan()
    churn_distribution = services.get_churn_distribution()
    hourly_distribution = services.get_hourly_distribution()
    total_revenue = services.get_total_revenue()
    
    context = {
        'sales_by_plan': sales_by_plan,
        'revenue_by_plan': revenue_by_plan,
        'popular_plan': popular_plan,
        'churn_distribution': churn_distribution,
        'hourly_distribution': json.dumps(hourly_distribution),
        'total_revenue': total_revenue,
        'page_title': 'Reports',
    }
    return render(request, 'pages/reports.html', context)
