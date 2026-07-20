from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('feedback', views.FeedbackViewset, basename='feedback')

urlpatterns = [
    path('dashboard/', views.FarmerDashboard.as_view(), name='farmer-dashboard'),
    path('my-collections/', views.FarmerCollection.as_view(), name='farmer-collections'),
    path('notices/', views.FarmerNoticeView.as_view(), name='farmer-notices'),
    path('predict-disease/', views.predict_disease, name='predict-disease'),
    path('valid-symptoms/', views.get_valid_symptoms, name='valid-symptoms'),
    path('', include(router.urls)),
]
