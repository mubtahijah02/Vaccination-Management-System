from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Child, CustomUser, Hospital, Parent, VaccinationRecord

class ParentForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class HospitalForm(UserCreationForm):
    name = forms.CharField(max_length=50, label='Hospital name')
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'name', 'phone', 'address', 'password1', 'password2']


class HospitalProfileForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['name', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ParentContactForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data['date_of_birth']
        if date_of_birth > timezone.localdate():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        return date_of_birth


class VaccinationRecordForm(forms.ModelForm):
    dose_number = forms.IntegerField(min_value=1, initial=1)
    hospital = forms.ModelChoiceField(
        queryset=Hospital.objects.none(),
        required=False,
        empty_label='No hospital selected',
    )

    class Meta:
        model = VaccinationRecord
        fields = ['vaccine_name', 'dose_number', 'scheduled_date', 'hospital']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hospital'].queryset = Hospital.objects.order_by('name')


class VaccinationCompletionForm(forms.Form):
    administered_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def clean_administered_date(self):
        administered_date = self.cleaned_data['administered_date']
        if administered_date > timezone.localdate():
            raise forms.ValidationError('Administered date cannot be in the future.')
        return administered_date