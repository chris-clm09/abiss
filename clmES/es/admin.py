from es.models import roles
from es.models import appointments
from es.models import times
from es.models import days
from es.models import UserProfile
from django.contrib import admin

admin.site.register(roles)
admin.site.register(appointments)
admin.site.register(times)
admin.site.register(days)
admin.site.register(UserProfile)
