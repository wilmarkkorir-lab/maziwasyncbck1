from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.AddMilkCollection, name='add-milk-collection'),
    path('my-collections/', views.MyCollections.as_view(), name='my-collections'),
    path('dashboard/', views.PorterDashboard, name='porter-dashboard'),
    path('notices/', views.PorterNoticeView.as_view(), name='porter-notices'),
]
