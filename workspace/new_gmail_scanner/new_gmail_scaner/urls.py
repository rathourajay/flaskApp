from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
                       # mapping the application with application url.
                       url(r'^gmail_app/', include('gmail_app.urls')),
                       url(r'^login/', include('login.urls')),
                       )
