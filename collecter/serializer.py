from rest_framework import serializers
from core.models import MilkCollection, Feedback, Notice


class RecentCollectionSerializer(serializers.ModelSerializer):
    farmer = serializers.StringRelatedField()
    porter = serializers.StringRelatedField()

    class Meta:
        model = MilkCollection
        fields = ['id', 'farmer', 'porter', 'litres', 'session', 'collection_date', 'total_amount', 'price_per_litre']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'description', 'status', 'created_at']
        read_only_fields = ('status', 'created_at')


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['id', 'title', 'message', 'target', 'is_important', 'created_at']