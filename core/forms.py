from django import forms
from .models import MembershipPlan, Member, MembershipPass


class MembershipPlanForm(forms.ModelForm):
    """Form for creating/editing membership plans"""
    class Meta:
        model = MembershipPlan
        fields = ['name', 'duration_days', 'price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter plan name'
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of days',
                'min': 1
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price in PHP',
                'step': '0.01',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class MemberForm(forms.ModelForm):
    """Form for creating/editing members"""
    class Meta:
        model = Member
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter member name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number (optional)'
            }),
        }


class SellPassForm(forms.Form):
    """Form for selling a new pass"""
    member = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a member"
    )
    membership_plan = forms.ModelChoiceField(
        queryset=MembershipPlan.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a plan"
    )

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        if member and member.has_active_pass():
            raise forms.ValidationError(
                f"{member.name} already has an active pass. "
                "Wait for it to expire before selling a new one."
            )
        return cleaned_data


class CheckInForm(forms.Form):
    """Form for quick check-in"""
    member = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a member to check in"
    )

    def clean_member(self):
        member = self.cleaned_data.get('member')
        if member and not member.has_active_pass():
            raise forms.ValidationError(
                f"{member.name} does not have an active pass. "
                "Please sell a pass first."
            )
        return member
