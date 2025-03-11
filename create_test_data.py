#!/usr/bin/env python
import os
import django
import sys
from datetime import datetime, timedelta, time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import models
from businesses.models import Business, Employee, Service, Shift, TimeSlot
from django.contrib.auth.models import User

def create_test_data():
    """Create test data for the booking system"""
    print("Creating test data...")
    
    # Get or create a test business
    try:
        business = Business.objects.first()
        if not business:
            # Create a test user
            user, created = User.objects.get_or_create(
                username='testuser',
                defaults={
                    'email': 'test@example.com',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                user.set_password('password')
                user.save()
                print("Created test user: testuser / password")
            
            # Create a test business
            business = Business.objects.create(
                owner=user,
                name='Test Barbershop',
                description='A test barbershop',
                address='123 Test St',
                phone='123-456-7890',
                email='test@example.com',
                opening_hours={
                    "0": {"open": "09:00", "close": "18:00"},
                    "1": {"open": "09:00", "close": "18:00"},
                    "2": {"open": "09:00", "close": "18:00"},
                    "3": {"open": "09:00", "close": "18:00"},
                    "4": {"open": "09:00", "close": "18:00"},
                    "5": {"open": "10:00", "close": "16:00"},
                    "6": {"open": "00:00", "close": "00:00"}
                }
            )
            print(f"Created test business: {business.name}")
    except Exception as e:
        print(f"Error creating business: {e}")
        return
    
    # Create test services
    services = []
    service_data = [
        {'name': 'Haircut', 'price': 25.00, 'duration': 30},
        {'name': 'Beard Trim', 'price': 15.00, 'duration': 20},
        {'name': 'Shave', 'price': 20.00, 'duration': 25},
        {'name': 'Hair Coloring', 'price': 50.00, 'duration': 60}
    ]
    
    for data in service_data:
        service, created = Service.objects.get_or_create(
            business=business,
            name=data['name'],
            defaults={
                'description': f"Standard {data['name']}",
                'price': data['price'],
                'duration': data['duration']
            }
        )
        services.append(service)
        if created:
            print(f"Created service: {service.name}")
    
    # Create test barbers
    barbers = []
    barber_data = [
        {'name': 'John Doe', 'email': 'john@example.com'},
        {'name': 'Jane Smith', 'email': 'jane@example.com'}
    ]
    
    for data in barber_data:
        barber, created = Employee.objects.get_or_create(
            business=business,
            name=data['name'],
            defaults={
                'email': data['email'],
                'phone': '123-456-7890'
            }
        )
        if created:
            # Add services to barber
            for service in services:
                barber.services.add(service)
            print(f"Created barber: {barber.name}")
        barbers.append(barber)
    
    # Create shifts for barbers
    for barber in barbers:
        # Create recurring shifts for weekdays
        for day in range(5):  # Monday to Friday
            shift, created = Shift.objects.get_or_create(
                business=business,
                employee=barber,
                shift_type='recurring',
                day_of_week=day,
                defaults={
                    'start_time': time(9, 0),  # 9:00 AM
                    'end_time': time(17, 0),   # 5:00 PM
                    'is_active': True
                }
            )
            if created:
                print(f"Created shift for {barber.name} on day {day}")
                
                # Generate time slots for this shift for the next occurrence
                try:
                    slots = shift.generate_time_slots(slot_duration=30)
                    print(f"Generated {len(slots)} time slots for {barber.name} on day {day}")
                except Exception as e:
                    print(f"Error generating time slots: {e}")
    
    print("Test data creation complete!")

if __name__ == '__main__':
    create_test_data() 