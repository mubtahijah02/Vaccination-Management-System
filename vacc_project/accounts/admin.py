from django.contrib import admin
from .models import Child, CustomUser, Hospital, Parent, VaccinationRecord


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Parent)
admin.site.register(Hospital)
admin.site.register(Child)
admin.site.register(VaccinationRecord)