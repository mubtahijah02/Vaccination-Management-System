from functools import wraps

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ChildForm,
    HospitalForm,
    ParentContactForm,
    ParentForm,
    VaccinationCompletionForm,
    VaccinationRecordForm,
)
from .models import Child, Hospital, Parent, VaccinationRecord


# Create your views here.
def home(request):
    return render(request, 'home.html')


def role_required(role):
    def decorator(view_func):
        @login_required(login_url='login')
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.role != role:
                return HttpResponseForbidden('You do not have permission to view this page.')
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def _parent_profile(user):
    parent, _ = Parent.objects.get_or_create(user=user)
    return parent


def register_parent(request):
    if request.method == 'POST':
        form = ParentForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.role = 'parent'
            user.save()
            Parent.objects.create(user = user)
            login(request, user)
            return redirect('parent_dashboard')
    else:
        form = ParentForm()
    return render(request, 'register_parent.html',{'form':form})

def register_hospital(request):
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.role = 'hospital'
            user.save()
            Hospital.objects.create(user = user)
            login(request, user)
            return redirect('hospital_dashboard')
    else:
        form = HospitalForm()
    return render(request, 'register_hospital.html',{'form':form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'hospital':
                return redirect('hospital_dashboard')
            elif user.role == 'parent':
                return redirect('parent_dashboard')
            logout(request)
            form.add_error(None, 'This account does not have a supported role.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/')


@role_required('admin')
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@role_required('hospital')
def hospital_dashboard(request):
    return render(request, 'hospital_dashboard.html')


@role_required('parent')
def parent_dashboard(request):
    parent = _parent_profile(request.user)
    children = Child.objects.filter(parent=parent).prefetch_related('vaccinations')
    return render(request, 'parent_dashboard.html', {
        'parent': parent,
        'children': children,
        'today': timezone.localdate(),
    })


@role_required('parent')
def parent_profile_update(request):
    parent = _parent_profile(request.user)
    form = ParentContactForm(request.POST or None, instance=parent)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your contact details have been updated.')
        return redirect('parent_dashboard')
    return render(request, 'parent_form.html', {
        'form': form,
        'title': 'Contact details',
        'eyebrow': 'FAMILY ACCOUNT',
        'intro': 'Keep your contact information up to date.',
        'submit_label': 'Save contact details',
        'cancel_url': 'parent_dashboard',
    })


@role_required('parent')
def child_add(request):
    parent = _parent_profile(request.user)
    form = ChildForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        child = form.save(commit=False)
        child.parent = parent
        child.save()
        messages.success(request, f'{child.name} has been added to your family account.')
        return redirect('parent_dashboard')
    return render(request, 'parent_form.html', {
        'form': form,
        'title': 'Add a child',
        'eyebrow': 'FAMILY ACCOUNT',
        'intro': 'Add a child profile to keep family-entered vaccine dates together.',
        'submit_label': 'Add child',
        'cancel_url': 'parent_dashboard',
    })


@role_required('parent')
def vaccination_add(request, child_id):
    parent = _parent_profile(request.user)
    child = get_object_or_404(Child, pk=child_id, parent=parent)
    form = VaccinationRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.child = child
        record.save()
        messages.success(request, f'{record.vaccine_name} was added for {child.name}.')
        return redirect('parent_dashboard')
    return render(request, 'parent_form.html', {
        'form': form,
        'title': f'Add a vaccine date for {child.name}',
        'eyebrow': 'FAMILY-ENTERED RECORD',
        'intro': 'Enter the vaccine and date provided by your child’s healthcare professional.',
        'submit_label': 'Save vaccine date',
        'cancel_url': 'parent_dashboard',
    })


@role_required('parent')
@require_POST
def vaccination_mark_completed(request, vaccination_id):
    parent = _parent_profile(request.user)
    record = get_object_or_404(
        VaccinationRecord,
        pk=vaccination_id,
        child__parent=parent,
    )
    form = VaccinationCompletionForm(request.POST)
    if form.is_valid():
        record.status = VaccinationRecord.COMPLETED
        record.administered_date = form.cleaned_data['administered_date']
        record.full_clean()
        record.save(update_fields=['status', 'administered_date'])
        messages.success(request, f'{record.vaccine_name} was marked completed.')
    else:
        messages.error(request, 'Enter a valid administered date to complete this record.')
    return redirect('parent_dashboard')