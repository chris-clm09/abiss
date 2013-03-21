import datetime
from datetime import timedelta
import sys
import locale as _locale

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, render

import django.contrib.auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import django.contrib.auth.views

from es.models import *

home = "/es/"
main = "/es/stuff/"
THE_DAYS = ("SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY")

#====================================================================================
# Day of the week...starting at 0 for sunday
#====================================================================================
def datetodayD(date):
    return datetoday(date.day, date.month, date.year)
def datetoday(day, month, year):
    d = day
    m = month
    y = year
    if m < 3:
        z = y-1
    else:
        z = y
    dayofweek = ( 23*m//9 + d + 4 + y + z//4 - z//100 + z//400 )
    if m >= 3:
        dayofweek -= 2
    dayofweek = dayofweek%7
    return dayofweek

#====================================================================================
#==============================Date Generator========================================
class Calendar(object):
    """
    Base calendar class. This class doesn't do any formatting. It simply
    provides data to subclasses.
    """

    def __init__(self, firstweekday=0):
        self.firstweekday = firstweekday # 0 = Monday, 6 = Sunday

    def getfirstweekday(self):
        return self._firstweekday % 7

    def setfirstweekday(self, firstweekday):
        self._firstweekday = firstweekday

    firstweekday = property(getfirstweekday, setfirstweekday)

    def itermonthdatesdays(self, year, month, theday):
        """
        Return an iterator for one month. The iterator will yield datetime.date
        values and will always iterate through complete weeks, so it will yield
        dates outside the specified month.
        """
        date = datetime.date(year, month, 1)
        # Go back to the beginning of the week
        days = (date.weekday() - self.firstweekday) % 7
        date -= datetime.timedelta(days=days)
        oneday = datetime.timedelta(days=1)
        while True:
            if date.month == month:
                if datetoday(date.day, date.month, date.year) == theday:
                    yield date
            try:
                date += oneday
            except OverflowError:
                # Adding one day could fail after datetime.MAXYEAR
                break
            if date.month != month and date.weekday() == self.firstweekday:
                break
#===============================End Date Generator===================================
#====================================================================================

#====================================================================================
# Get the current user's bishop.
#====================================================================================
def getUsersBishop(request):
    esUser = UserProfile.objects.get(username=request.user.username)
    return UserProfile.objects.get(id=esUser.bishop)

#====================================================================================
# Contoller that compiles the needed data to display the main
# calandar page.  This page shows all of the apointments for a given bishop
# and month.
#====================================================================================
@login_required
def index(request):
    #Get Start Of the Month
    currentDate = datetime.date.today()
    date        = currentDate - timedelta(days=currentDate.day - 1)
    
    #Get Month Data
    strMonth        = currentDate.strftime("%B")
    myBishop        = getUsersBishop(request).id
    thedays         = days.objects.filter(bishop=myBishop, to_display=True)
    theappointments = appointments.objects.filter(bishop=myBishop, date__gte=date)
    
    
    fDays = []
    map_days_monthDates = {}
    map_days_rows       = {}
    map_aptsId_apts     = {}
    for iDays in thedays:
        t_fDays = THE_DAYS[iDays.day_index_from_sunday]
        fDays.append(t_fDays)
        
        l = []
        c = Calendar()
        for rDate in c.itermonthdatesdays(currentDate.year,
                                          currentDate.month,
                                          iDays.day_index_from_sunday):
		if rDate >= currentDate:            	
			l.append(rDate)
        
        map_days_monthDates.update({t_fDays:l})
        
        #Get Times
        thetimes = times.objects.filter(bishop=myBishop, to_display=True, day=iDays.id)
        #gen appointments table for day
        rows = []
        for t in thetimes:
            r = []
            r.append(t.time.strftime("%I:%M %p"))
            for d in l:
                aptInfo = getAppointmentInfo(d, t, theappointments)
                r.append(aptInfo[0])
                if aptInfo[0] > 0:
                    map_aptsId_apts.update({aptInfo[0]:aptInfo[1]})
            rows.append(r)
            
        map_days_rows.update({t_fDays:rows})
    
    return render_to_response('stuff/index.html', {'month': strMonth,
                                                   'days': fDays,
                                                   'mDaysToMntDays': map_days_monthDates,
                                                   'mDaysToRows': map_days_rows,
                                                   'mAptsIdToApts': map_aptsId_apts})

#====================================================================================
# Given a day and time and list of appointments, this function will return
# the appoinment that matches both the day and time.
#====================================================================================
def getAppointmentInfo(d, t, appointments):
    #print "D:", d,"| T:", t, "|A:", appointments
    for appointment in appointments:
        if appointment.date == d:
            #print "Dates Matched: ","D:", d,"| T:", t, "|AT:", appointment.time, "|Teq?", appointment.time.time == t.time,"|", type(t),"|", type(appointment.time) ,"A:", appointment
            if appointment.time.time == t.time:
                return [appointment.id, appointment]
            
    return [encodeDayAndTime(d, t)]

#====================================================================================
# Encodes a date and time into a single number and then negates it.
#====================================================================================
def encodeDayAndTime(d, t):
    day    = d.day * 10000
    hour   = int(t.time.strftime("%H")) * 100
    minute = int(t.time.strftime("%M"))
    return -(day + hour + minute)

#====================================================================================
# Decodes encodeDayAndTime
#====================================================================================
def decodeDayAndTime(e):
    n = -e
    day =  n / 10000
    n   -= (day * 10000)
    
    hour =  n / 100
    n    -= (hour * 100)
    
    minute = n
    
    now = datetime.datetime.now()
    dateAndTime = datetime.datetime(now.year, now.month, day, hour, minute, 0)
    return [dateAndTime.date(), dateAndTime.time()]
  
#====================================================================================
# This function control the creation of an appointment.
#====================================================================================
def add(request, addcode):
    
    dt = decodeDayAndTime(int(addcode))
    
    if request.method == 'GET':
        form = AppointmentForm()
        return render_to_response('stuff/add.html', {'form':form,
                                                     'code':addcode,
                                                     'date':dt[0],
                                                     'time':dt[1].strftime("%I:%M %p")},
                                  context_instance=RequestContext(request))
    if request.method =='POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('es.views.index'))  
        form = AppointmentForm(request.POST)
        if not form.is_valid():
            return render_to_response('stuff/add.html', {'form':form,
                                                         'code':addcode,
                                                         'date':dt[0],
                                                         'time':dt[1].strftime("%I:%M %p")},
                                      context_instance=RequestContext(request))
        
        a = appointments()
        a.the_appointment = form.cleaned_data['appointment']
        a.bishop = getUsersBishop(request)
        a.date = dt[0]
        theday = days.objects.get(day_index_from_sunday=datetodayD(dt[0]), bishop=a.bishop)
        a.time = times.objects.get(time=dt[1], day=theday)
        a.save()
        
        return HttpResponseRedirect(reverse('es.views.index'))  

#====================================================================================
# This function will control the editing of an appointment.
#====================================================================================
@login_required
def edit(request, theid):
    try:
        a = appointments.objects.get(id=theid)
    except:
        raise Http404
    
    if request.method == 'GET':
        form = AppointmentForm(initial={'appointment': a.the_appointment})
        
        return render_to_response('stuff/edit.html', {'form':form,
                                                     'id':theid,
                                                     'date':a.date,
                                                     'time':a.time},
                                  context_instance=RequestContext(request))
    if request.method =='POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('es.views.index'))  
        form = AppointmentForm(request.POST)
        if not form.is_valid():
            return render_to_response('stuff/edit.html', {'form':form,
                                                         'id':theid,
                                                         'date':a.date,
                                                         'time':a.time},
                                      context_instance=RequestContext(request))
    if 'rmv' in request.POST:
        a.delete()
    
    if 'mod' in request.POST:
        a.the_appointment = form.cleaned_data['appointment']
        a.save()
    
    return HttpResponseRedirect(reverse('es.views.index'))  


#====================================================================================
# Controler for the functionality to set which days are displayed, and to set
# which times for those days are displayed.
#====================================================================================
@login_required
def editDailyTimes(request):
    theDays = days.objects.filter(bishop=getUsersBishop(request))
    
    links = {}
    for aDay in theDays:
        alink = 0
        if aDay.to_display:
            alink = -aDay.id
        else:
            alink = aDay.id
        links.update({THE_DAYS[aDay.day_index_from_sunday]:alink})
    
    if request.method == 'GET':
        return render_to_response('stuff/editDailyTimes.html', {'days':THE_DAYS,
                                                                'links':links},
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        if not form.is_valid():
            return render_to_response('stuff/editDailyTimes.html', {'days':THE_DAYS,
                                                                    'links':links},
                                  context_instance=RequestContext(request))
    return render_to_response('stuff/editDailyTimes.html', {'stuff': request.user.username })

#====================================================================================
# This function will set the given day(dayid) to be displayed.
#====================================================================================
@login_required
def displayDay(request, dayid):
    day = days.objects.get(id=dayid)
    day.to_display = True
    day.save()
    return HttpResponseRedirect(reverse('es.views.editDailyTimes'))

#====================================================================================
# This function will set the given day(dayid) not to by displayed.
#====================================================================================
@login_required
def dontDisplayDay(request, dayid):
    day = days.objects.get(id=-int(dayid))
    day.to_display = False
    day.save()
    return HttpResponseRedirect(reverse('es.views.editDailyTimes'))

#====================================================================================
# This function will set the given time(timeid) to be displayed.
#====================================================================================
@login_required
def displayTime(request, timeid, dayoffset):
    time = times.objects.get(id=int(timeid))
    time.to_display = True
    time.save()
    return HttpResponseRedirect("/es/stuff/setDayTimes/" + str(dayoffset) + "/")

#====================================================================================
# This function will set the given time(timeid) not to be displayed.
#====================================================================================
@login_required
def dontDisplayTime(request, timeid, dayoffset):
    time = times.objects.get(id=-int(timeid))
    time.to_display = False
    time.save()
    return HttpResponseRedirect("/es/stuff/setDayTimes/" + str(dayoffset) + "/")

#====================================================================================
# This function will take a set of 85 times and seperate them into a list
# of five columns.
#====================================================================================
def getFiveColumnTimes(theday):
    thetimes = times.objects.filter(day=theday)
    i = 0
    li = 0
    dlist = [[],[],[],[],[]]
    while i < len(thetimes):
        dlist[li].append(thetimes[i])
        i += 1
        if i % 33 == 0 and li < 4:
            li += 1
    return dlist

#====================================================================================
# This function will first element off the ith list and append it to row.
#====================================================================================
def popFirstTime(row, fiveTimes, i):
    add = fiveTimes[i][0]
    row.append(add.time.strftime("%I:%M %p"))
    fiveTimes[i].remove(add)
    
    if add.to_display:
        row.append(-add.id)
    else:
        row.append(add.id)
            
    return [row, fiveTimes]

#====================================================================================
# This controler will display all of the times for a given day and their
# current state.
#====================================================================================
@login_required
def setDayTimes(request, dayoffset):
    theday = days.objects.get(bishop=getUsersBishop(request), day_index_from_sunday=int(dayoffset))

    #Split up times in a 5 * 17 manner
    fiveCTimes = getFiveColumnTimes(theday)

    #Generate table
    table = []
    for i in range(33):
        row = []
        temp = popFirstTime(row, fiveCTimes, 0)    
        temp = popFirstTime(temp[0], temp[1], 1)
        temp = popFirstTime(temp[0], temp[1], 2)
        temp = popFirstTime(temp[0], temp[1], 3)
        temp = popFirstTime(temp[0], temp[1], 4)
        table.append(temp[0])

    return render_to_response('stuff/setDayTimes.html', {'day':THE_DAYS[int(dayoffset)],
                                                         'times': table,
                                                         'dayoffset': dayoffset})


#====================================================================================
# Logs a user into the system.
#====================================================================================
def login(request):
    if request.method == 'GET':
        form = LoginForm()
        next = home + "stuff/"
        return render_to_response('auth/login.html', {'form':form,
                                                      'next':next,
                                                      'login':True},
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render_to_response('auth/login.html', {'form':form,
                                                          'login':True},
                                  context_instance=RequestContext(request))

        auser = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
        if auser is None:
            return render_to_response('auth/login.html',
                                      {'form':form, 'login':True,
                                       'error': 'Invalid username or password'},
                                      context_instance=RequestContext(request))
        django.contrib.auth.login(request,auser)
        
        try:
            esUser = UserProfile.objects.get(username=auser.username)
        except UserProfile.DoesNotExist:
            return render_to_response('auth/login.html',
                                      {'form':form, 'login':True,
                                       'error': 'Not an ES user yet: contact admin'},
                                      context_instance=RequestContext(request))
        #todo: Transition Pages
        return HttpResponseRedirect("/es/stuff/")
    
#====================================================================================
# Logs a user out of the system.
#====================================================================================
def logout(request):
    django.contrib.auth.logout(request)
    return HttpResponseRedirect(reverse('es.views.login'))

#====================================================================================
# This function will allow a user to change their password.
#====================================================================================
@login_required
def changeMyPassword(request):
    if request.method == 'GET':
        form = ChangePassword()
        return render_to_response('auth/changeMyPassword.html', {'form':form},
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        if 'done' in request.POST:
            return HttpResponseRedirect(reverse('es.views.index'))  
        form = ChangePassword(request.POST)
        if not form.is_valid():
            return render(request, 'auth/changeMyPassword.html', {'form':form})
    
    try:
        request.user.set_password(form.cleaned_data['password'])
        request.user.save()
    except:
        if not form.is_valid():
            return render(request, 'auth/changeMyPassword.html', {'form':form,
                                                                  'error':"Framework error! Please contact admin. Your password was not changed."})
     
    return HttpResponseRedirect(reverse('es.views.index'))  


#--------------------------------Create New User--------------------------------#

#====================================================================================
# Creates a new user for the system.  If a bishop is added then the appropriate
# entries are added in the database for days and times. 
#====================================================================================
@login_required
def create(request):
    if request.method == 'GET':
        form = NewUserForm()
        next = main
        return render_to_response('auth/create.html', {'form':form,
                                                      'next':next},
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        if 'done' in request.POST:
            return HttpResponseRedirect(reverse('es.views.index'))  
        form = NewUserForm(request.POST)
        if not form.is_valid():
            return render(request, 'auth/create.html', {'form':form})
        else:
            if form.cleaned_data['role'].id != 1:
                if form.cleaned_data['bishop'] == None:
                      return render_to_response('auth/create.html',
                                          {'form':form, 'error':"Must select a bishop."},
                                  context_instance=RequestContext(request))
                
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                nuser = User.objects.create_user(username, None, password)
            except:
                return render_to_response('auth/create.html',
                                          {'form':form, 'error':"Your username already exists."},
                                  context_instance=RequestContext(request))
            
            userP          = UserProfile()
            userP.username = username
            userP.role     = form.cleaned_data['role']
            userP.save()
            
            if userP.role.id == 1:
               userP.bishop = userP.id
            else:
               userP.bishop = form.cleaned_data['bishop'].id
            
            try:
               userP.save()
            except:
                nuser.delete()
                userP.delete()
                return render_to_response('auth/create.html',
                                          {'form':form, 'error':"Error saveing es user. Contanct Admin."},
                                 context_instance=RequestContext(request))
            if userP.role.id == 1:
                popTableForNewBishop(userP)
    
    
    return HttpResponseRedirect(reverse('es.views.index'))

#====================================================================================
# Poplates the days and times tables with the appropreate data.
#====================================================================================
def popTableForNewBishop(theNewBishop):
    numDaysOfTheWeek = 7
    for i in range(numDaysOfTheWeek):
        newDay = days()
        newDay.bishop = theNewBishop
        newDay.day_index_from_sunday = i
        newDay.save()
        
        time = datetime.datetime(2000, 1, 1, 7, 0, 0)
        for t in range(168):
            newTime            = times()
            newTime.bishop     = theNewBishop
            newTime.day        = newDay
            newTime.to_display = False
            newTime.time       = time.time()
            newTime.save()
            
            time = time + timedelta(minutes=5)
    
    
    


