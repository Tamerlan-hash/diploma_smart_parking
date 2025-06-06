# serializers.py
from rest_framework import serializers
from .models import ParkingSpot, Sensor, Blocker

class BlockerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocker
        fields = (
            'reference',
            'is_raised',
            'created_at',
        )

class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = (
            'reference',
            'is_occupied',
            'created_at',
        )

class ParkingSpotSerializer(serializers.ModelSerializer):
    is_reserved = serializers.SerializerMethodField()
    sensor = SensorSerializer(read_only=True)
    blocker = BlockerSerializer(read_only=True)
    is_occupied = serializers.SerializerMethodField()
    is_blocker_raised = serializers.SerializerMethodField()

    class Meta:
        model = ParkingSpot
        fields = (
            'reference',
            'name',
            'latitude1',
            'latitude2',
            'latitude3',
            'latitude4',
            'longitude1',
            'longitude2',
            'longitude3',
            'longitude4',
            'price_per_hour',
            'is_reserved',
            'is_occupied',
            'is_blocker_raised',
            'sensor',
            'blocker',
            'created_at',
        )

    def get_is_reserved(self, obj):
        return obj.is_reserved()

    def get_is_occupied(self, obj):
        if hasattr(obj, 'sensor'):
            return obj.sensor.is_occupied
        return False

    def get_is_blocker_raised(self, obj):
        if hasattr(obj, 'blocker'):
            return obj.blocker.is_raised
        return False
