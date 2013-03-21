from django.db import models
from django.contrib.auth.models import User
from django import forms

class roles(models.Model):
   role_name = models.CharField('role_name',max_length=50)
   
   def __unicode__(self):
        return self.role_name

class appointments(models.Model):
   the_appointment = models.CharField('the_appointment', max_length=256)
   time = models.ForeignKey('times')
   date = models.DateField('date')
   bishop = models.ForeignKey('UserProfile')
   
   def __unicode__(self):
        return self.the_appointment

class days(models.Model):
   day_index_from_sunday = models.IntegerField('day_index_from_sunday')
   bishop = models.ForeignKey('UserProfile')
   to_display = models.BooleanField()

class times(models.Model):
   day = models.ForeignKey('days')
   time = models.TimeField('time')
   bishop = models.ForeignKey('UserProfile')
   to_display = models.BooleanField()
   
   def __unicode__(self):
        return self.time.strftime("%I:%M %p")
      
class UserProfile(models.Model):
   username = models.CharField('username', max_length=256, unique=True)
   role = models.ForeignKey('roles')
   bishop = models.IntegerField('bishop', null=True)
   def __unicode__(self):
        return self.username
   
class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False),
                               max_length=100)

class ChangePassword(forms.Form):
   password = forms.CharField(widget=forms.PasswordInput(render_value=False),
                               max_length=100)   
    
class AppointmentForm(forms.Form):
   appointment = forms.CharField(max_length=256)
    
class NewUserForm(forms.Form):
    username = forms.CharField(max_length=256)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False),
                               max_length=100)
    role = forms.ModelChoiceField(queryset=roles.objects.all())
    bishop = forms.ModelChoiceField(queryset=UserProfile.objects.filter(role=1), required=False)
    