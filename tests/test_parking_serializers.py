import pytest
from django.utils import timezone
from datetime import timedelta
import uuid
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from sensor.models import Sensor, ParkingSpot
from parking.models import Reservation
from parking.serializers import ReservationSerializer, ReservationDetailSerializer, ReservationListSerializer

@pytest.mark.django_db
class TestReservationSerializer:
    """Test the ReservationSerializer validation logic."""

    @pytest.fixture
    def setup_data(self):
        """Set up test data for serializer tests."""
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # First create a ParkingSpot
        parking_spot = ParkingSpot.objects.create(
            reference=uuid.uuid4(),
            name='Test Parking Spot'
        )
        # Then create a Sensor associated with the ParkingSpot
        sensor = Sensor.objects.create(
            reference=uuid.uuid4(),
            parking_spot=parking_spot
        )

        # Set up time variables
        now = timezone.now()
        # Ensure start_time is at the beginning of an hour
        start_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        end_time = (now + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

        # Create a request context
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user

        return {
            'user': user,
            'sensor': sensor,
            'now': now,
            'start_time': start_time,
            'end_time': end_time,
            'request': request
        }

    def test_serializer_valid_data(self, setup_data):
        """Test that the serializer accepts valid data."""
        data = setup_data

        serializer_data = {
            'parking_spot': data['sensor'].parking_spot.reference,
            'start_time': data['start_time'],
            'end_time': data['end_time']
        }

        serializer = ReservationSerializer(
            data=serializer_data,
            context={'request': data['request']}
        )

        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"

    def test_serializer_end_time_before_start_time(self, setup_data):
        """Test that the serializer rejects end_time before start_time."""
        data = setup_data

        serializer_data = {
            'parking_spot': data['sensor'].parking_spot.reference,
            'start_time': data['start_time'],
            'end_time': data['start_time'] - timedelta(hours=1)  # End time before start time
        }

        serializer = ReservationSerializer(
            data=serializer_data,
            context={'request': data['request']}
        )

        assert not serializer.is_valid()
        assert "End time must be after start time" in str(serializer.errors)

    def test_serializer_start_time_in_past(self, setup_data):
        """Test that the serializer rejects start_time in the past."""
        data = setup_data

        serializer_data = {
            'parking_spot': data['sensor'].parking_spot.reference,
            'start_time': data['now'] - timedelta(hours=1),  # Start time in the past
            'end_time': data['now'] + timedelta(hours=1)
        }

        serializer = ReservationSerializer(
            data=serializer_data,
            context={'request': data['request']}
        )

        assert not serializer.is_valid()
        assert "Start time cannot be in the past" in str(serializer.errors)

    def test_serializer_overlapping_reservation(self, setup_data):
        """Test that the serializer rejects overlapping reservations."""
        data = setup_data

        # Create an existing reservation
        Reservation.objects.create(
            user=data['user'],
            parking_spot=data['sensor'].parking_spot,
            start_time=data['start_time'],
            end_time=data['end_time'],
            status='pending'
        )

        # Try to create an overlapping reservation (using the same time slot)
        serializer_data = {
            'parking_spot': data['sensor'].parking_spot.reference,
            'start_time': data['start_time'],
            'end_time': data['end_time']
        }

        serializer = ReservationSerializer(
            data=serializer_data,
            context={'request': data['request']}
        )

        assert not serializer.is_valid()
        assert "already reserved" in str(serializer.errors)

    def test_serializer_update_exclude_current(self, setup_data):
        """Test that the serializer excludes the current reservation when updating."""
        data = setup_data

        # Create a reservation
        reservation = Reservation.objects.create(
            user=data['user'],
            parking_spot=data['sensor'].parking_spot,
            start_time=data['start_time'],
            end_time=data['end_time'],
            status='pending'
        )

        # Update the same reservation (should be valid since it excludes itself)
        # Use a different hour but still at the beginning of an hour
        serializer_data = {
            'parking_spot': data['sensor'].parking_spot.reference,
            'start_time': data['start_time'] + timedelta(hours=1),
            'end_time': data['end_time'] + timedelta(hours=1)
        }

        serializer = ReservationSerializer(
            instance=reservation,
            data=serializer_data,
            context={'request': data['request']}
        )

        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"

    def test_serializer_create_sets_user(self, setup_data):
        """Test that the serializer sets the user to the request user when creating."""
        data = setup_data

        serializer_data = {
            'parking_spot': data['sensor'].parking_spot.reference,
            'start_time': data['start_time'],
            'end_time': data['end_time']
        }

        serializer = ReservationSerializer(
            data=serializer_data,
            context={'request': data['request']}
        )

        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"

        reservation = serializer.save()

        assert reservation.user == data['user']

    def test_serializer_missing_parking_spot(self, setup_data):
        """Test that the serializer rejects data without parking_spot."""
        data = setup_data

        serializer_data = {
            'start_time': data['start_time'],
            'end_time': data['end_time']
        }

        serializer = ReservationSerializer(
            data=serializer_data,
            context={'request': data['request']}
        )

        assert not serializer.is_valid()
        assert "parking_spot" in serializer.errors
        assert "This field is required." in str(serializer.errors["parking_spot"])

@pytest.mark.django_db
class TestReservationDetailSerializer:
    """Test the ReservationDetailSerializer."""

    @pytest.fixture
    def setup_data(self):
        """Set up test data for serializer tests."""
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # First create a ParkingSpot
        parking_spot = ParkingSpot.objects.create(
            reference=uuid.uuid4(),
            name='Test Parking Spot'
        )
        # Then create a Sensor associated with the ParkingSpot
        sensor = Sensor.objects.create(
            reference=uuid.uuid4(),
            parking_spot=parking_spot
        )

        # Set up time variables
        now = timezone.now()
        # Ensure start_time is at the beginning of an hour
        start_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        end_time = (now + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

        # Create a reservation
        reservation = Reservation.objects.create(
            user=user,
            parking_spot=parking_spot,
            start_time=start_time,
            end_time=end_time,
            status='pending'
        )

        return {
            'user': user,
            'sensor': sensor,
            'reservation': reservation
        }

    def test_detail_serializer_includes_sensor_details(self, setup_data):
        """Test that the detail serializer includes sensor details."""
        data = setup_data

        serializer = ReservationDetailSerializer(data['reservation'])

        assert 'parking_spot' in serializer.data
        assert serializer.data['parking_spot']['name'] == data['sensor'].parking_spot.name
        assert serializer.data['parking_spot']['reference'] == str(data['sensor'].parking_spot.reference)

@pytest.mark.django_db
class TestReservationListSerializer:
    """Test the ReservationListSerializer."""

    @pytest.fixture
    def setup_data(self):
        """Set up test data for serializer tests."""
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # First create a ParkingSpot
        parking_spot = ParkingSpot.objects.create(
            reference=uuid.uuid4(),
            name='Test Parking Spot'
        )
        # Then create a Sensor associated with the ParkingSpot
        sensor = Sensor.objects.create(
            reference=uuid.uuid4(),
            parking_spot=parking_spot
        )

        # Set up time variables
        now = timezone.now()
        # Ensure start_time is at the beginning of an hour
        start_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        end_time = (now + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

        # Create a reservation
        reservation = Reservation.objects.create(
            user=user,
            parking_spot=parking_spot,
            start_time=start_time,
            end_time=end_time,
            status='pending'
        )

        return {
            'user': user,
            'sensor': sensor,
            'reservation': reservation
        }

    def test_list_serializer_includes_parking_spot_name(self, setup_data):
        """Test that the list serializer includes the parking spot name."""
        data = setup_data

        serializer = ReservationListSerializer(data['reservation'])

        assert 'parking_spot_name' in serializer.data
        assert serializer.data['parking_spot_name'] == data['sensor'].parking_spot.name

    def test_list_serializer_excludes_user(self, setup_data):
        """Test that the list serializer excludes the user field."""
        data = setup_data

        serializer = ReservationListSerializer(data['reservation'])

        assert 'user' not in serializer.data
