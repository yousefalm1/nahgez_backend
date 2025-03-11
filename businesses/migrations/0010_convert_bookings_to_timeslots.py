from django.db import migrations
from datetime import datetime, timedelta

def convert_bookings_to_timeslots(apps, schema_editor):
    """
    Convert existing bookings to use the new time slot system.
    This creates a shift for each employee and time slots for each booking.
    """
    Booking = apps.get_model('businesses', 'Booking')
    Shift = apps.get_model('businesses', 'Shift')
    TimeSlot = apps.get_model('businesses', 'TimeSlot')
    
    # Get all bookings that don't have a time_slot yet
    bookings = Booking.objects.filter(time_slot__isnull=True)
    
    for booking in bookings:
        # Skip if missing required data
        if not booking.date or not booking.time or not booking.employee:
            continue
        
        # Calculate end time (assume 1 hour duration if not specified)
        duration = booking.service.duration if hasattr(booking.service, 'duration') else 60
        start_datetime = datetime.combine(booking.date, booking.time)
        end_datetime = start_datetime + timedelta(minutes=duration)
        end_time = end_datetime.time()
        
        # Get or create a shift for this employee on this day of week
        day_of_week = booking.date.weekday()
        shift, created = Shift.objects.get_or_create(
            business=booking.business,
            employee=booking.employee,
            day_of_week=day_of_week,
            defaults={
                'start_time': booking.time,
                'end_time': end_time,
                'is_active': True
            }
        )
        
        # Create a time slot for this booking
        time_slot = TimeSlot.objects.create(
            shift=shift,
            date=booking.date,
            start_time=booking.time,
            end_time=end_time,
            is_available=False  # Already booked
        )
        
        # Link the booking to the time slot
        booking.time_slot = time_slot
        booking.save()

def reverse_convert(apps, schema_editor):
    """
    No need to reverse this migration as we're keeping the legacy fields.
    """
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0009_alter_booking_options_alter_booking_date_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_bookings_to_timeslots, reverse_convert),
    ] 