from django.conf.urls import  patterns,url
from gmail_app import views
urlpatterns = patterns('' ,
                       url(r'^$', views.first_page),
                        url(r'^gmail_scanner/',views.gmail_scanner, name="gmail_scanner"),    
                       )