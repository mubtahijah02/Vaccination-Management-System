from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('hospital', 'Hospital'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    def __str__(self):
        return f"{self.username} ({self.role})"

class Parent(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    def __str__(self):
        return self.user.username

class Hospital(models.Model):

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=50,  blank=True )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True)
    def __str__(self):
        return self.name


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_of_birth', 'name']

    def __str__(self):
        return self.name


class VaccinationRecord(models.Model):
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (COMPLETED, 'Completed'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='vaccinations')
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        related_name='vaccination_appointments',
        blank=True,
        null=True,
    )
    completed_by_hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        related_name='confirmed_vaccinations',
        blank=True,
        null=True,
    )
    vaccine_name = models.CharField(max_length=120)
    dose_number = models.PositiveSmallIntegerField(default=1)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=SCHEDULED)
    administered_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'vaccine_name', 'dose_number']

    def clean(self):
        if self.status == self.COMPLETED and self.administered_date is None:
            raise ValidationError({'administered_date': 'Enter the date this dose was administered.'})
        if self.status == self.SCHEDULED and self.administered_date is not None:
            raise ValidationError({'administered_date': 'Scheduled doses cannot have an administered date.'})
        if self.completed_by_hospital_id and self.status != self.COMPLETED:
            raise ValidationError({'completed_by_hospital': 'Only completed doses can be confirmed by a hospital.'})
        if self.completed_by_hospital_id and self.completed_by_hospital_id != self.hospital_id:
            raise ValidationError({'completed_by_hospital': 'Only the assigned hospital can confirm this dose.'})

    def __str__(self):
        return f'{self.vaccine_name} dose {self.dose_number} for {self.child}'