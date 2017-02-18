from django.conf.urls import url
from . import views

app_name = 'gdriveapi'
urlpatterns = [
    url(r'^sync/$', views.SyncView.as_view()),
]
