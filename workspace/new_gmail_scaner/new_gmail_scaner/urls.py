from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^gmail_app/', include('gmail_app.urls')), #mapping the application with application url.
)
