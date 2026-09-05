from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from collecter.serializer import RecentCollectionSerializer, FeedbackSerializer, NoticeSerializer
from core.models import FarmerProfile, Feedback, MilkCollection, Notice
from django.db.models import Sum
from datetime import date
from django.utils import timezone
from rest_framework.response import Response



# farmer darshboard
class FarmerDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            farmer = request.user.farmer_profile
        except FarmerProfile.DoesNotExist:
            raise PermissionDenied("Only farmers can view the dashboard")
        collections = MilkCollection.objects.filter(farmer=farmer).order_by('-created_at')[:5]
        total_collections = collections.count()
        total_litres = collections.aggregate(total=Sum('litres'))['total'] or 0
        total_amount = collections.aggregate(total=Sum('total_amount'))['total'] or 0

        today_litres = (
            MilkCollection.objects
            .filter(farmer=farmer, collection_date=date.today())
            .aggregate(total=Sum('litres'))['total'] or 0
        )

        monthly_litres = (
            MilkCollection.objects
            .filter(farmer=farmer, collection_date__month=date.today().month)
            .aggregate(total=Sum('litres'))['total'] or 0
        )
        monthly_earning = (
            MilkCollection.objects
            .filter(farmer=farmer, collection_date__month=date.today().month)
            .aggregate(total=Sum('total_amount'))['total'] or 0
        )
        today_collections = (
            MilkCollection.objects
            .filter(farmer=farmer, collection_date=date.today())
            .count()
        )
        return Response({
            'total_collections': total_collections,
            'total_litres': total_litres,
            'total_amount': total_amount,
            'today_collection': today_collections,
            'monthly_litres': monthly_litres,
            'monthly_earning': monthly_earning,
        })


# ======================================================================

class FarmerCollection(generics.ListAPIView):  
    serializer_class = RecentCollectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            farmer = self.request.user.farmer_profile
        except FarmerProfile.DoesNotExist:
            raise PermissionDenied("Only farmers can view their collections")
        collections=(
            MilkCollection.objects
            .filter(farmer=farmer)
            .select_related('porter')
            .order_by('-created_at')

        )
        return collections


# ================================================================
# feedbackoperations
# ===============================================================
class FeedbackViewset(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            farmer=self.request.user.farmer_profile
        except:
            raise PermissionDenied("only farmers can access this end point")
        return (
            Feedback.objects
            .filter(farmer=farmer)
            .order_by('-created_at')
        )
    # post
    def perform_create(self, serializer):
        try:
            farmer = self.request.user.farmer_profile
        except FarmerProfile.DoesNotExist:
            raise PermissionDenied("only farmers can give feedback")
        serializer.save(farmer=farmer)


# notices
class FarmerNoticeView(generics.ListAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        notices=(
            Notice.objects
            .filter(target__in=['all','farmers'])
            .order_by('-created_at')
        )
        return notices
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def predict_disease(request):
    animal = request.data.get('animal')
    age = request.data.get('age')
    temp = request.data.get('Temperature')
    description = request.data.get('Description')

    from farmer.services import CattleAIService
    ai_service = CattleAIService()
    result = ai_service.predict(animal_type=animal, age=age, temp=temp, description=description)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_valid_symptoms(request):
    from farmer.services import CattleAIService
    ai_service = CattleAIService()
    return Response({"valid_symptoms": ai_service.valid_symptoms})