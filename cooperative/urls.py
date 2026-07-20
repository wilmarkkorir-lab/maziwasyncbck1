from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('farmers', views.FarmerViewSet, basename='farmers')
router.register('porters', views.PorterViewSet, basename='porters')
router.register('collections', views.MilkCollectionViewSet, basename='collections')
router.register('notices', views.NoticeViewSet, basename='notices')

urlpatterns = [
    path('dashboard/', views.AdminDashboardData.as_view(), name='admin-dashboard'),
    path('farmers-balance/', views.FarmersWithBal, name='farmers-balance'),
    path('pay-farmer/', views.pay_farmer, name='pay-farmer'),
    path('callback/', views.MpesaCallBack, name='mpesa-callback'),
    path('', include(router.urls)),
]
