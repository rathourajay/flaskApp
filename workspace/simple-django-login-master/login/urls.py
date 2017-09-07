from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
admin.autodiscover()
from django.views.generic.base import RedirectView
from login import views

urlpatterns = [
    #     url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    #     url(r'^login/$', auth_views.login,
    #         {'template_name': 'login.html'}, name='login'),
    #     url(r'^logout/$', auth_views.logout,
    #         {'template_name': 'logged_out.html'}, name='logout'),

    url(r'^gmail_scanner/', views.gmail_scanner, name="gmail_scanner"),
    url(r'^.*$', RedirectView.as_view(url='gmail_scanner/',
                                          permanent=False), name='index')
]
