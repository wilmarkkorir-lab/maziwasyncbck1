from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers, generics
from core.models import FarmerProfile, Notice, PorterProfile, MilkCollection
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from collecter.serializer import RecentCollectionSerializer, NoticeSerializer


# porter dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def PorterDashboard(request):
    try:
        porter = request.user.porter_profile
    except PorterProfile.DoesNotExist:
        return Response({"error": "Porter profile not found"})
    # time settings
    today = timezone.now().date()
    week_start=today-timedelta(days=7)
    monthly_start = today.replace(day=1)

    # today collection
    todays_collection = MilkCollection.objects.filter(porter=porter,collection_date=today)
    total_litres_today = todays_collection.count()
    total_litres_today=todays_collection.aggregate(total=Sum('litres'))["total"] or 0
    total_amount_today=todays_collection.aggregate(total=Sum('total_amount'))["total"] or 0
    # weekly collection
    weekly_collection = MilkCollection.objects.filter(porter=porter, collection_date__gte=(week_start))
    total_litres_weekly = weekly_collection.aggregate(total=Sum('litres'))["total"] or 0
    # monthly collection
    monthly_collection = MilkCollection.objects.filter(porter=porter, collection_date__gte=(monthly_start))
    total_litres_monthly = monthly_collection.aggregate(total=Sum('litres'))["total"] or 0
    # current 5 collections
    last_collections = MilkCollection.objects.filter(porter=porter).order_by('created_at')[:5]


    # serialize multiple milk collection record since last_collections is a queryset -multiple objects
    last_collections_list=RecentCollectionSerializer(
        last_collections, 
        many=True
        ).data

    response_date={
        'date':today,
        'assigned_farmers':porter.assigned_farmers.count(),
        'total_litres_today':total_litres_today,
        'total_amount_today':total_amount_today,
        'total_litres_weekly':total_litres_weekly,
        'total_litres_monthly':total_litres_monthly,
        'last_collections':last_collections_list,
        'porter_name':f"{porter.first_name} {porter.last_name}",
        'route_name':porter.route_name,
        'employee_id':porter.employee_id,
    }
    return Response(response_date)


class MilkCollectionSerializer(serializers.ModelSerializer):
    porter = serializers.StringRelatedField()
    farmer = serializers.StringRelatedField()

    class Meta:
        model = MilkCollection
        fields = ['id', 'porter', 'farmer', 'litres', 'session', 'collection_date', 'total_amount', 'price_per_litre']


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AddMilkCollection(request):
    try:
        porter = request.user.porter_profile
    except PorterProfile.DoesNotExist:
        return Response({"error": "Only porter can add milk collection"}, status=403)

    try:
        farmer = FarmerProfile.objects.get(national_id=request.data.get('national_id'))
    except FarmerProfile.DoesNotExist:
        return Response({"error": "Farmer not found"}, status=404)

    collection = MilkCollection.objects.create(
        porter=porter,
        farmer=farmer,
        litres=request.data.get('litres'),
        session=request.data.get('session'),
    )
    return Response({
        "message": "Milk collection recorded successfully",
        "collection_id": collection.id,
        "farmer": f"{farmer.first_name} {farmer.last_name}",
        "porter": f"{porter.first_name} {porter.last_name}",
        "litres": collection.litres,
        "total_amount": collection.total_amount,
    }, status=201)
# view porter collections list

class MyCollections(generics.ListAPIView):
    serializer_class = MilkCollectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        porter = self.request.user.porter_profile
        colections = (
            MilkCollection.objects
            .filter(porter=porter)
            .select_related('farmer')
            .order_by('created_at')
        )
        return colections


class PorterNoticeView(generics.ListAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        notices=(
            Notice.objects
            .filter(target__in=['all','porters'])
            .order_by('-created_at')
        )
        return notices


        
