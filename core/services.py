"""
Business Logic, Analytics, ML, and AI Prompt Builders
"""
from django.db.models import Count, Sum, F
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import numpy as np

from .models import Member, MembershipPlan, MembershipPass, Attendance


# =============================================================================
# DASHBOARD ANALYTICS
# =============================================================================

def get_today_checkins():
    """Count today's check-ins"""
    today = timezone.now().date()
    return Attendance.objects.filter(
        checked_in_at__date=today
    ).count()


def get_active_passes_count():
    """Count currently active passes"""
    today = timezone.now().date()
    return MembershipPass.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        status='active'
    ).count()


def get_expired_passes_count():
    """Count expired passes"""
    today = timezone.now().date()
    # Update expired passes first
    MembershipPass.objects.filter(
        end_date__lt=today,
        status='active'
    ).update(status='expired')
    
    return MembershipPass.objects.filter(status='expired').count()


def get_revenue_today():
    """Sum of price_snapshot for passes sold today"""
    today = timezone.now().date()
    result = MembershipPass.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('price_snapshot'))
    return result['total'] or Decimal('0.00')


def get_total_revenue():
    """Total revenue from all passes"""
    result = MembershipPass.objects.aggregate(total=Sum('price_snapshot'))
    return result['total'] or Decimal('0.00')


# =============================================================================
# PEAK TIME ANALYTICS
# =============================================================================

def get_peak_hour():
    """
    Determine the peak hour of check-ins.
    Returns tuple: (peak_hour, count) or (None, 0) if no data
    """
    peak_data = Attendance.objects.annotate(
        hour=ExtractHour('checked_in_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    if peak_data:
        return (peak_data['hour'], peak_data['count'])
    return (None, 0)


def format_peak_hour(hour):
    """Format hour (0-23) to readable time range"""
    if hour is None:
        return "No data"
    
    start_hour = hour
    end_hour = (hour + 1) % 24
    
    def format_time(h):
        if h == 0:
            return "12:00 AM"
        elif h < 12:
            return f"{h}:00 AM"
        elif h == 12:
            return "12:00 PM"
        else:
            return f"{h-12}:00 PM"
    
    return f"{format_time(start_hour)} – {format_time(end_hour)}"


def get_hourly_distribution():
    """Get check-in distribution by hour for charts"""
    distribution = Attendance.objects.annotate(
        hour=ExtractHour('checked_in_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Create full 24-hour distribution
    hours = {i: 0 for i in range(24)}
    for item in distribution:
        hours[item['hour']] = item['count']
    
    return hours


# =============================================================================
# REPORTS ANALYTICS
# =============================================================================

def get_sales_count_by_plan():
    """Count of passes sold per plan"""
    return MembershipPass.objects.values(
        'membership_plan__name'
    ).annotate(
        count=Count('id'),
        plan_name=F('membership_plan__name')
    ).order_by('-count')


def get_revenue_by_plan():
    """Total revenue per plan"""
    return MembershipPass.objects.values(
        'membership_plan__name'
    ).annotate(
        total=Sum('price_snapshot'),
        plan_name=F('membership_plan__name')
    ).order_by('-total')


def get_most_popular_plan():
    """Get the most sold plan"""
    result = get_sales_count_by_plan()
    if result:
        top = list(result)[0]
        return top['plan_name']
    return "N/A"


# =============================================================================
# MEMBER ANALYTICS & CHURN PREDICTION
# =============================================================================

def calculate_member_features(member):
    """
    Calculate features for a member for ML prediction.
    Returns: (days_left_on_pass, attendance_last_7_days, attendance_last_3_days)
    """
    today = timezone.now().date()
    now = timezone.now()
    
    # Days left on pass
    active_pass = member.get_active_pass()
    if active_pass:
        days_left = (active_pass.end_date - today).days + 1
    else:
        days_left = 0
    
    # Attendance in last 7 days
    seven_days_ago = now - timedelta(days=7)
    attendance_7 = Attendance.objects.filter(
        member=member,
        checked_in_at__gte=seven_days_ago
    ).count()
    
    # Attendance in last 3 days
    three_days_ago = now - timedelta(days=3)
    attendance_3 = Attendance.objects.filter(
        member=member,
        checked_in_at__gte=three_days_ago
    ).count()
    
    return (days_left, attendance_7, attendance_3)


def predict_churn(member):
    """
    Simple Logistic Regression churn prediction.
    Returns: (return_probability, churn_risk_level)
    
    Uses scikit-learn if available, otherwise uses a simple heuristic.
    """
    days_left, attendance_7, attendance_3 = calculate_member_features(member)
    
    try:
        from sklearn.linear_model import LogisticRegression
        
        # Get training data from all members
        members = Member.objects.all()
        X = []
        y = []
        
        for m in members:
            features = calculate_member_features(m)
            X.append(list(features))
            # Synthetic labels: return if attendance >= 2 in last 7 days
            y.append(1 if features[1] >= 2 else 0)
        
        if len(X) >= 3 and len(set(y)) > 1:  # Need enough data and both classes
            X = np.array(X)
            y = np.array(y)
            
            model = LogisticRegression(random_state=42, max_iter=1000)
            model.fit(X, y)
            
            # Predict for this member
            member_features = np.array([[days_left, attendance_7, attendance_3]])
            prob = model.predict_proba(member_features)[0][1]
        else:
            # Fallback heuristic
            prob = calculate_heuristic_probability(days_left, attendance_7, attendance_3)
    
    except ImportError:
        # scikit-learn not available, use heuristic
        prob = calculate_heuristic_probability(days_left, attendance_7, attendance_3)
    
    # Determine risk level
    if prob >= 0.7:
        risk_level = 'Low'
    elif prob >= 0.4:
        risk_level = 'Medium'
    else:
        risk_level = 'High'
    
    return (round(prob, 2), risk_level)


def calculate_heuristic_probability(days_left, attendance_7, attendance_3):
    """Fallback heuristic when ML is not available"""
    score = 0
    
    # Days left contribution (max 0.3)
    if days_left > 5:
        score += 0.3
    elif days_left > 2:
        score += 0.2
    elif days_left > 0:
        score += 0.1
    
    # Attendance 7 days contribution (max 0.4)
    if attendance_7 >= 4:
        score += 0.4
    elif attendance_7 >= 2:
        score += 0.25
    elif attendance_7 >= 1:
        score += 0.1
    
    # Attendance 3 days contribution (max 0.3)
    if attendance_3 >= 2:
        score += 0.3
    elif attendance_3 >= 1:
        score += 0.15
    
    return min(score, 1.0)


def get_churn_distribution():
    """
    Get distribution of members by churn risk level.
    Returns: {'High': count, 'Medium': count, 'Low': count}
    """
    distribution = {'High': 0, 'Medium': 0, 'Low': 0}
    
    for member in Member.objects.all():
        _, risk_level = predict_churn(member)
        distribution[risk_level] += 1
    
    return distribution


def get_high_churn_count():
    """Count members with high churn risk"""
    return get_churn_distribution()['High']


# =============================================================================
# RETURN VOLUME PREDICTION
# =============================================================================

def get_expected_returns_next_3_days():
    """
    Estimate expected returns in the next 3 days based on churn predictions.
    
    Expected Returns = (Likely Returners * 0.8) + (Maybe Returners * 0.4)
    """
    likely_returners = 0  # prob >= 0.7
    maybe_returners = 0   # 0.4 <= prob < 0.7
    unlikely_returners = 0  # prob < 0.4
    
    for member in Member.objects.all():
        prob, _ = predict_churn(member)
        if prob >= 0.7:
            likely_returners += 1
        elif prob >= 0.4:
            maybe_returners += 1
        else:
            unlikely_returners += 1
    
    expected = (likely_returners * 0.8) + (maybe_returners * 0.4)
    
    return {
        'likely_returners': likely_returners,
        'maybe_returners': maybe_returners,
        'unlikely_returners': unlikely_returners,
        'expected_returns': round(expected, 1)
    }


# =============================================================================
# AI INSIGHTS PROMPT BUILDERS
# =============================================================================

def build_dashboard_prompt():
    """
    Build AI prompt for dashboard insights.
    """
    today_checkins = get_today_checkins()
    active_passes = get_active_passes_count()
    expired_passes = get_expired_passes_count()
    revenue_today = get_revenue_today()
    peak_hour, peak_count = get_peak_hour()
    peak_time = format_peak_hour(peak_hour)
    expected_data = get_expected_returns_next_3_days()
    popular_plan = get_most_popular_plan()
    high_churn = get_high_churn_count()
    
    prompt = f"""Act as a gym business analyst. Based on this operational and predictive data, give 3 short insights and 2 actionable recommendations.

OPERATIONAL DATA:
- Today's Check-ins: {today_checkins}
- Active Passes: {active_passes}
- Expired Passes: {expired_passes}
- Revenue Today: ₱{revenue_today}
- Peak Time: {peak_time} ({peak_count} check-ins)

PREDICTIVE DATA:
- Expected Returns (Next 3 Days): {expected_data['expected_returns']}
- Most Popular Plan: {popular_plan}
- High Churn Risk Members: {high_churn}

Provide insights in a concise, actionable format."""
    
    return prompt


def build_member_prompt(member):
    """
    Build AI prompt for member-specific retention insights.
    """
    prob, risk_level = predict_churn(member)
    days_left, attendance_7, attendance_3 = calculate_member_features(member)
    
    prompt = f"""Based on this member behavior data, give a short retention recommendation.

MEMBER: {member.name}
- Return Probability: {prob * 100:.0f}%
- Churn Risk Level: {risk_level}
- Days Left on Pass: {days_left}
- Attendance (Last 7 Days): {attendance_7}
- Attendance (Last 3 Days): {attendance_3}

Provide a brief, personalized retention recommendation."""
    
    return prompt


def generate_dashboard_insights():
    """
    Generate AI insights for the dashboard.
    This is a placeholder that simulates AI response.
    Hook-ready for future OpenAI integration.
    """
    today_checkins = get_today_checkins()
    active_passes = get_active_passes_count()
    high_churn = get_high_churn_count()
    peak_hour, _ = get_peak_hour()
    expected_data = get_expected_returns_next_3_days()
    
    insights = []
    recommendations = []
    
    # Generate contextual insights
    if today_checkins == 0:
        insights.append("📊 No check-ins recorded today yet. Consider sending reminder notifications to members with active passes.")
    elif today_checkins < 5:
        insights.append(f"📊 Light traffic today with {today_checkins} check-ins. Good opportunity for equipment maintenance.")
    else:
        insights.append(f"📊 Strong engagement today with {today_checkins} check-ins!")
    
    if high_churn > 0:
        insights.append(f"⚠️ {high_churn} member(s) show high churn risk. Consider proactive outreach.")
    else:
        insights.append("✅ No high-risk churn members currently. Retention efforts are working well.")
    
    if peak_hour is not None:
        peak_time = format_peak_hour(peak_hour)
        insights.append(f"⏰ Peak activity occurs at {peak_time}. Ensure adequate staffing during this time.")
    
    # Generate recommendations
    if active_passes < 5:
        recommendations.append("🎯 Run a promotional campaign to boost new pass sales.")
    else:
        recommendations.append("🎯 Maintain current marketing efforts. Pass sales are healthy.")
    
    if expected_data['maybe_returners'] > 0:
        recommendations.append(f"📱 Send personalized messages to {expected_data['maybe_returners']} 'maybe' returners to encourage visits.")
    else:
        recommendations.append("📱 Focus retention efforts on building habits for new members.")
    
    return {
        'insights': insights,
        'recommendations': recommendations,
        'prompt': build_dashboard_prompt()
    }


def generate_member_insights(member):
    """
    Generate AI insights for a specific member.
    This is a placeholder that simulates AI response.
    """
    prob, risk_level = predict_churn(member)
    days_left, attendance_7, attendance_3 = calculate_member_features(member)
    
    recommendation = ""
    
    if risk_level == 'High':
        if attendance_7 == 0:
            recommendation = "🚨 Member hasn't visited recently. Send a personalized 'We miss you' message with an incentive to return."
        else:
            recommendation = "⚠️ Engagement is declining. Consider offering a personal training session or class recommendation."
    elif risk_level == 'Medium':
        if days_left <= 2:
            recommendation = "📅 Pass expiring soon. Reach out about renewal options before it expires."
        else:
            recommendation = "📊 Moderate engagement. Encourage more frequent visits to build a consistent habit."
    else:  # Low risk
        if attendance_7 >= 3:
            recommendation = "⭐ Highly engaged member! Consider loyalty rewards or referral incentives."
        else:
            recommendation = "✅ Good standing. Continue providing excellent service to maintain satisfaction."
    
    return {
        'recommendation': recommendation,
        'prompt': build_member_prompt(member),
        'return_probability': prob,
        'risk_level': risk_level,
        'days_left': days_left,
        'attendance_7': attendance_7,
        'attendance_3': attendance_3
    }
