from django.conf.urls.defaults import *
from clmES.settings import ROOT

urlpatterns = patterns('es.views',
                       url(r'^stuff/$', 'index'),
                       
                       url(r'^stuff/editDailyTimes/$', 'editDailyTimes'),
                       url(r'^stuff/editDailyTimes$', 'editDailyTimes'),
                       
                       url(r'^auth/login/$', 'login'),
                       url(r'^auth/login$', 'login'),
                       
                       url(r'^auth/logout/$', 'logout'),
                       url(r'^auth/logout$', 'logout'),
                       
                       url(r'^auth/create/$', 'create'),
                       url(r'^auth/create$', 'create'),
                       
                       url(r'^auth/changeMyPassword/$', 'changeMyPassword'),
                       url(r'^auth/changeMyPassword$', 'changeMyPassword'),
                       
                       url(r'^stuff/add/(?P<addcode>-\d+)/$', 'add'),
                       url(r'^stuff/edit/(?P<theid>\d+)/$', 'edit'),
                       
                       url(r'^stuff/dday/(?P<dayid>\d+)/$', 'displayDay'),
                       url(r'^stuff/ddday/(?P<dayid>-\d+)/$', 'dontDisplayDay'),
                       
                       url(r'^stuff/dtime/(?P<timeid>\d+)/(?P<dayoffset>\d+)/$', 'displayTime'),
                       url(r'^stuff/ddtime/(?P<timeid>-\d+)/(?P<dayoffset>\d+)/$', 'dontDisplayTime'),
                       
                       url(r'^stuff/setDayTimes/(?P<dayoffset>\d+)/$', 'setDayTimes'),
                       )

urlpatterns += patterns('',
                       (r'^static/(?P<path>.*)$',
                        'django.views.static.serve',
                        {'document_root': ROOT('es/static/')})
                       )

