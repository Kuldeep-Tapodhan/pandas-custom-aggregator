from django.urls import path
from . import views

urlpatterns = [
    path('', views.aggregation_view, name='aggregation_view'),
]