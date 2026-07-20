from rest_framework import serializers
from core.models import FarmerProfile, Notice, PorterProfile


class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = '__all__'


class PorterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PorterProfile
        fields = '__all__'

# notices 
class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = '__all__'
        read_only_fields = ('created_by',)

        
