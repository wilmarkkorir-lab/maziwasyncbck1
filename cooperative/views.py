from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny
from core.models import FarmerProfile, Feedback, Notice, PorterProfile, MilkCollection, Payment
from cooperative.serializer import FarmerSerializer, NoticeSerializer, PorterSerializer
from collecter.serializer import RecentCollectionSerializer
from django.db.models import Sum
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

# admin/cooperative dashboard
from rest_framework.views import APIView

from cooperative.services import MpesaPayment


class AdminDashboardData(APIView):
    def get(self, request):
        # define the dates according  to django timezone settings
        # used for daily ,weekly and monthly calculations
        today = timezone.now().date()
        # calculate the start of the week 7 days
        week_start = today - timedelta(days=7)

        # farmer and porter stats
        total_farmers = FarmerProfile.objects.count()
        total_porters = PorterProfile.objects.count()
        # daily , weekly and monthly collections
        # we will retrieve all the collection so that we can reuse
        collections = MilkCollection.objects.all()

        total_litres = collections.aggregate(total=Sum('litres'))['total'] or 0
        today_litres = collections.filter(collection_date=today).aggregate(total=Sum('litres'))['total'] or 0
        week_litres = collections.filter(collection_date__gte=week_start).aggregate(total=Sum('litres'))['total'] or 0
        month_litres = collections.filter(
            collection_date__year=today.year,
            collection_date__month=today.month
        ).aggregate(total=Sum('litres'))['total'] or 0

        total_amount = collections.aggregate(total=Sum('total_amount'))['total'] or 0
        today_earning = collections.filter(collection_date=today).aggregate(total=Sum('total_amount'))['total'] or 0
        week_earning = collections.filter(collection_date__gte=week_start).aggregate(total=Sum('total_amount'))['total'] or 0
        month_earning = collections.filter(
            collection_date__year=today.year,
            collection_date__month=today.month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        # feedback analytics
        pending_feedbacks = Feedback.objects.filter(status='pending').count()
        pending_resolved=Feedback.objects.filter(status='resolved').count()

        # Top Farmers- retrieve farmers with highest milk delivery
        top_farmers = FarmerProfile.objects.annotate(
            total_delivered=Sum('milk_collections__litres')
        ).order_by('-total_delivered')[:5]
        top_farmers_data=FarmerSerializer(
            top_farmers,
            many=True

        ).data
        # top ten  latest milk collections
        Recent_Collections = MilkCollection.objects.select_related('farmer', 'porter').order_by('-created_at')[:10]
        # convert the collection objects to json data
        Recent_Collections_data = RecentCollectionSerializer(
            Recent_Collections,
            many=True
        ).data
        # dashboard response
        return Response({
            'total_farmers': total_farmers,
            'total_porters': total_porters,
            'total_litres': total_litres,
            'total_amount': total_amount,
            'today_litres': today_litres,
            'today_earning': today_earning,
            'week_litres':week_litres,
            'week_earning':week_earning,
            'month_litres':month_litres,
            'month_earning':month_earning,
            'pending_feedbacks': pending_feedbacks,
            'resolved_feedbacks':pending_resolved,
            'top_farmers':top_farmers_data,
            'recent_collections':Recent_Collections_data,
    })
    
    
    




      





        



     


class FarmerViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.all()
    serializer_class = FarmerSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'put', 'patch', 'delete']


class PorterViewSet(viewsets.ModelViewSet):
    queryset = PorterProfile.objects.all()
    serializer_class = PorterSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'put', 'patch', 'delete']

class MilkCollectionViewSet(viewsets.ModelViewSet):
    queryset = MilkCollection.objects.select_related('farmer', 'porter')
    serializer_class = RecentCollectionSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'put', 'patch', 'delete']

    # Notices board by the cooperative
class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

        # GET farmers with outstanding arreas/balances

@api_view(['GET'])
@permission_classes([IsAdminUser])
def FarmersWithBal(request):
    farmers=FarmerProfile.objects.all()
    data=[]
    for farmer in farmers:
        # amount earned by the farmer
        earned=MilkCollection.objects.filter(farmer=farmer).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # amount paid to the farmer
        paid=Payment.objects.filter(farmer=farmer).aggregate(
            total=Sum('amount')
        )['total'] or 0

        balance= earned-paid
        if balance >0:
            data.append({
               "farmer_id":farmer.id,
               "farmer_name":f"{farmer.first_name} {farmer.last_name}",
               "phone_number":farmer.phone_number,
               "balance":balance,
               "earned":earned,
                "paid":paid,
               "balance":balance
              
            })
    return Response(data)

# initiate the disburtments to the farmer
@api_view(['POST'])
@permission_classes([IsAdminUser])
def pay_farmer(request):
    farmer_id = request.data.get('farmer_id')
    amount = request.data.get('amount')

    try:
        farmer = FarmerProfile.objects.get(id=farmer_id)
    except FarmerProfile.DoesNotExist:
        return Response({'error': 'Farmer not found'}, status=404)

    earned = MilkCollection.objects.filter(farmer=farmer).aggregate(total=Sum('total_amount'))['total'] or 0
    paid = Payment.objects.filter(farmer=farmer).aggregate(total=Sum('amount'))['total'] or 0
    balance = earned - paid

    if balance <= 0:
        return Response({'message': 'No payment pending'})

    mpesa = MpesaPayment()
    result = mpesa.pay_farmer(farmer.mpesa_number or farmer.phone_number, amount)

    Payment.objects.create(
        farmer=farmer,
        amount=amount,
        payment_method='mpesa',
        transaction_ref=result.get('ConversationID', f'TXN-{farmer_id}'),
        originator_conversation_id=result.get('OriginatorConversationID'),
    )
    return Response({
        "farmer":f"{farmer.first_name} {farmer.last_name}",
        "prev_balance":balance,
        "mpesa_response":result
        })


# asynchronous callback processing webhook
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def MpesaCallBack(request):
    # extract the body of the request
    print("===== call back Hit =====")
    data = request.data

    # print the response from safaricom to see it in the terminal
    print("Data", data)
    result = data.get("Result", {})

    originator_conversation_id = result.get("OriginatorConversationID")
    try:
        payment_record = Payment.objects.get(originator_conversation_id=originator_conversation_id)
    except Payment.DoesNotExist:
        return Response({"status": "error", "message": "Payment record not found"}, status=404)

    if result.get("ResultCode") == 0:
        payment_record.status = "completed"
        payment_record.transaction_ref = result.get("TransactionID")
    else:
        payment_record.status = "failed"

    payment_record.save()
    return Response({"Received":True})



    

