from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import BusinessRequest, Business, Employee, Service, Shift, Booking, TimeSlot
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.hashers import make_password
from django.http import Http404, JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import uuid
import json
from datetime import datetime
from django.db import models

# Create your views here.

class BusinessRequestView(CreateView):
    model = BusinessRequest
    template_name = 'businesses/request_form.html'
    success_url = reverse_lazy('businesses:business_request_success')
    fields = [
        'business_name', 'first_name', 'last_name', 'business_type', 'description',
        'email', 'phone', 'whatsapp',
        'address', 'city',
        'instagram', 'facebook', 'website',
        'years_in_business', 'number_of_employees', 'services_offered',
        'has_business_license', 'business_license_number', 'additional_notes'
    ]

    def form_valid(self, form):
        messages.success(self.request, 'Your business request has been submitted successfully!')
        return super().form_valid(form)

def business_request_success(request):
    return render(request, 'businesses/request_success.html')

def business_account_setup(request, token):
    """
    View for business owners to set up their account
    The token is a simple hash of the business ID and email
    """
    # Decode the token to get the business ID
    try:
        import hashlib
        import base64
        
        # Decode the token
        decoded_token = base64.b64decode(token.encode()).decode()
        parts = decoded_token.split('|')
        if len(parts) != 2:
            raise Http404("Invalid token")
            
        business_id = int(parts[0])
        email_hash = parts[1]
        
        # Get the business
        business = get_object_or_404(Business, id=business_id)
        
        # Verify the email hash
        email_hash_check = hashlib.md5(business.email.encode()).hexdigest()
        if email_hash != email_hash_check:
            raise Http404("Invalid token")
            
        # Check if this business already has an active owner account
        if business.owner and business.owner.is_active:
            return render(request, 'businesses/account_setup.html', {
                'business': business,
                'error_message': 'This business already has an active account. Please contact support if you need assistance.'
            })
        
        # Handle form submission
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            full_name = request.POST.get('full_name')
            phone_number = request.POST.get('phone_number')
            
            # Validate form data
            if password != password2:
                return render(request, 'businesses/account_setup.html', {
                    'business': business,
                    'error_message': 'Passwords do not match'
                })
                
            if User.objects.filter(username=username).exists():
                return render(request, 'businesses/account_setup.html', {
                    'business': business,
                    'error_message': 'Username already exists'
                })
            
            # Split full name
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get or create business owners group with appropriate permissions
            business_owners_group, created = Group.objects.get_or_create(name='Business Owners')
            
            # If the group was just created, add appropriate permissions
            if created:
                # Add permissions for business owners to manage their own business data
                business_content_type = ContentType.objects.get_for_model(Business)
                service_content_type = ContentType.objects.get_for_model(Service)
                employee_content_type = ContentType.objects.get_for_model(Employee)
                booking_content_type = ContentType.objects.get_for_model(Booking)
                
                # Add view and change permissions for these models
                for content_type in [business_content_type, service_content_type, employee_content_type, booking_content_type]:
                    view_perm = Permission.objects.get(content_type=content_type, codename__startswith='view_')
                    change_perm = Permission.objects.get(content_type=content_type, codename__startswith='change_')
                    add_perm = Permission.objects.get(content_type=content_type, codename__startswith='add_')
                    business_owners_group.permissions.add(view_perm, change_perm, add_perm)
            
            # Handle the placeholder user
            placeholder_user = business.owner
            
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=business.email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Add user to the business owners group
            user.groups.add(business_owners_group)
            
            # Update business with the new owner and phone
            business.owner = user
            business.phone = phone_number
            business.save()
            
            # Delete the placeholder user if it exists
            if placeholder_user and placeholder_user.username.startswith('temp_'):
                placeholder_user.delete()
            
            # Redirect to success page
            return render(request, 'businesses/account_setup_success.html', {
                'business_name': business.name
            })
        
        return render(request, 'businesses/account_setup.html', {
            'business': business
        })
    except Exception as e:
        raise Http404("Invalid token")

def account_setup_success(request):
    """
    View for displaying the account setup success page
    """
    return render(request, 'businesses/account_setup_success.html')

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employees(request):
    """
    Get all employees for a business.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        # Get the business for the current user
        try:
            business = Business.objects.get(owner=request.user)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'No business found for this user'}, status=404)
        
        # Get all active employees for the business
        employees = Employee.objects.filter(business=business, is_active=True)
        
        return JsonResponse({
            'employees': [{
                'id': employee.id,
                'name': employee.name,
                'email': employee.email,
                'phone': employee.phone,
                'services': list(employee.services.values('id', 'name'))
            } for employee in employees]
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_employee(request):
    """
    Add a new employee to a business.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        # Get the business for the current user
        try:
            business = Business.objects.get(owner=request.user)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'No business found for this user'}, status=404)
        
        # Get data from request
        name = request.data.get('name')
        if not name:
            return JsonResponse({'error': 'Employee name is required'}, status=400)
            
        # Create the employee
        employee = Employee.objects.create(
            business=business,
            name=name,
            phone=request.data.get('phone'),
            email=request.data.get('email'),
            is_active=True
        )
        
        # Handle services if provided
        service_ids = request.data.get('services', [])
        if service_ids:
            # Verify all services belong to this business
            services = Service.objects.filter(
                id__in=service_ids,
                business=business
            )
            employee.services.set(services)
        
        return JsonResponse({
            'message': 'Employee added successfully',
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'phone': employee.phone,
                'email': employee.email,
                'services': list(employee.services.values('id', 'name'))
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_employee(request, employee_id):
    """
    Delete an employee from a business.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        # Get the business for the current user
        try:
            business = Business.objects.get(owner=request.user)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'No business found for this user'}, status=404)
        
        # Get the employee and verify it belongs to this business
        try:
            employee = Employee.objects.get(id=employee_id, business=business)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        # Delete the employee
        employee.delete()
        
        return JsonResponse({
            'message': 'Employee deleted successfully',
            'employee_id': employee_id
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_service(request):
    """
    Add a new service to a business.
    Requires authentication token in header: Authorization: Bearer <your_token>
    
    Expected POST data:
    {
        "name": "Service Name",
        "description": "Service Description",
        "duration": 30,  # in minutes
        "price": "50.00"
    }
    """
    try:
        # Get the business for the current user
        try:
            business = Business.objects.get(owner=request.user)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'No business found for this user'}, status=404)
        
        # Get data from request
        name = request.data.get('name')
        if not name:
            return JsonResponse({'error': 'Service name is required'}, status=400)
            
        description = request.data.get('description', '')
        duration = request.data.get('duration')  # in minutes
        price = request.data.get('price')
        
        # Validate duration
        try:
            duration = int(duration) if duration else None
        except ValueError:
            return JsonResponse({'error': 'Duration must be a number in minutes'}, status=400)
        
        # Validate price
        try:
            price = float(price) if price else None
        except ValueError:
            return JsonResponse({'error': 'Price must be a valid number'}, status=400)
            
        # Create the service
        service = Service.objects.create(
            business=business,
            name=name,
            description=description,
            duration=duration,
            price=price,
            is_active=True
        )
        
        return JsonResponse({
            'message': 'Service added successfully',
            'service': {
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'duration': service.duration,
                'price': str(service.price) if service.price else None
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def manage_shifts(request):
    """
    Get all shifts for a business.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        business = Business.objects.get(owner=request.user)
        shifts = Shift.objects.filter(business=business).select_related('employee')
        
        return JsonResponse({
            'shifts': [{
                'id': shift.id,
                'employee': {
                    'id': shift.employee.id,
                    'name': shift.employee.name,
                },
                'day_of_week': shift.day_of_week,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'is_active': shift.is_active
            } for shift in shifts]
        })
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_weekly_shifts(request):
    """
    Get shifts organized by day of the week.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        business = Business.objects.get(owner=request.user)
        shifts = Shift.objects.filter(business=business, is_active=True).select_related('employee')
        
        # Organize shifts by day
        weekly_shifts = {
            'Monday': [], 'Tuesday': [], 'Wednesday': [], 
            'Thursday': [], 'Friday': [], 'Saturday': [], 'Sunday': []
        }
        
        for shift in shifts:
            day = shift.get_day_of_week_display()
            weekly_shifts[day].append({
                'id': shift.id,
                'employee': {
                    'id': shift.employee.id,
                    'name': shift.employee.name,
                },
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
            })
        
        return JsonResponse({'weekly_shifts': weekly_shifts})
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_shift(request):
    """
    Add a new shift for an employee.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        # Get the business for the current user
        try:
            business = Business.objects.get(owner=request.user)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'No business found for this user'}, status=404)
        
        # Get data from request
        employee_id = request.data.get('employee_id')
        day_of_week = request.data.get('day_of_week')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        
        # Validate required fields
        if not all([employee_id, day_of_week is not None, start_time, end_time]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        # Convert times to datetime.time objects
        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid time format. Use HH:MM'}, status=400)
            
        # Validate employee belongs to this business
        try:
            employee = Employee.objects.get(id=employee_id, business=business)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
            
        # Check for overlapping shifts
        overlapping_shifts = Shift.objects.filter(
            employee=employee,
            day_of_week=day_of_week
        ).filter(
            models.Q(start_time__lt=end_time, end_time__gt=start_time)
        )
        
        if overlapping_shifts.exists():
            return JsonResponse({'error': 'This shift overlaps with an existing shift'}, status=400)
            
        # Create the shift
        shift = Shift.objects.create(
            business=business,
            employee=employee,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )
        
        # Time slots will be automatically generated in the Shift.save() method
        
        return JsonResponse({
            'message': 'Shift added successfully',
            'shift': {
                'id': shift.id,
                'employee': {
                    'id': employee.id,
                    'name': employee.name
                },
                'day_of_week': shift.get_day_of_week_display(),
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'is_active': shift.is_active
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_shift(request, shift_id):
    """
    Update an existing shift.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        business = Business.objects.get(owner=request.user)
        
        try:
            shift = Shift.objects.get(id=shift_id, business=business)
        except Shift.DoesNotExist:
            return JsonResponse({'error': 'Shift not found'}, status=404)
        
        # Update fields if provided
        if 'start_time' in request.data:
            try:
                shift.start_time = datetime.strptime(request.data['start_time'], '%H:%M').time()
            except ValueError:
                return JsonResponse({'error': 'Invalid start time format. Use HH:MM'}, status=400)
        
        if 'end_time' in request.data:
            try:
                shift.end_time = datetime.strptime(request.data['end_time'], '%H:%M').time()
            except ValueError:
                return JsonResponse({'error': 'Invalid end time format. Use HH:MM'}, status=400)
        
        if 'is_active' in request.data:
            shift.is_active = request.data['is_active']
        
        # Validate times
        if shift.start_time >= shift.end_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)
        
        # Check for overlapping shifts
        existing_shifts = Shift.objects.filter(
            employee=shift.employee,
            day_of_week=shift.day_of_week,
            is_active=True
        ).exclude(id=shift.id)
        
        for existing_shift in existing_shifts:
            if (shift.start_time < existing_shift.end_time and 
                shift.end_time > existing_shift.start_time):
                return JsonResponse({
                    'error': 'This shift overlaps with an existing shift'
                }, status=400)
        
        shift.save()
        
        return JsonResponse({
            'message': 'Shift updated successfully',
            'shift': {
                'id': shift.id,
                'employee': {
                    'id': shift.employee.id,
                    'name': shift.employee.name,
                },
                'day_of_week': shift.day_of_week,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'is_active': shift.is_active
            }
        })
        
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_shift(request, shift_id):
    """
    Delete a shift.
    Requires authentication token in header: Authorization: Bearer <your_token>
    """
    try:
        business = Business.objects.get(owner=request.user)
        
        try:
            shift = Shift.objects.get(id=shift_id, business=business)
        except Shift.DoesNotExist:
            return JsonResponse({'error': 'Shift not found'}, status=404)
        
        shift.delete()
        
        return JsonResponse({
            'message': 'Shift deleted successfully',
            'shift_id': shift_id
        })
        
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    Create a new booking with multiple services.
    
    Expected POST data:
    {
        "business_id": 1,
        "service_ids": [1, 2],  # List of service IDs
        "employee_id": 1,
        "date": "2024-03-15",
        "start_time": "10:00"
    }
    """
    try:
        # Get data from request
        business_id = request.data.get('business_id')
        service_ids = request.data.get('service_ids', [])
        employee_id = request.data.get('employee_id')
        date_str = request.data.get('date')
        start_time_str = request.data.get('start_time')
        
        # Validate required fields
        if not all([business_id, service_ids, employee_id, date_str, start_time_str]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get business and validate
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'Business not found'}, status=404)
            
        # Get employee and validate
        try:
            employee = Employee.objects.get(id=employee_id, business=business)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
            
        # Get services and validate
        services = Service.objects.filter(id__in=service_ids, business=business)
        if len(services) != len(service_ids):
            return JsonResponse({'error': 'One or more services not found'}, status=404)
            
        # Calculate total duration needed
        total_duration = sum(service.duration for service in services)
        required_slots = (total_duration + 29) // 30  # Round up to nearest 30-min slot
        
        # Parse date and time
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time format'}, status=400)
            
        # Get employee's shift for this day
        day_of_week = booking_date.weekday()
        shift = Shift.objects.filter(
            employee=employee,
            day_of_week=day_of_week,
            start_time__lte=start_time,
            end_time__gte=start_time,
            is_active=True
        ).first()
        
        if not shift:
            return JsonResponse({'error': 'No available shift found for this time'}, status=400)
            
        # Find consecutive available slots
        available_slots = TimeSlot.objects.filter(
            shift=shift,
            date=booking_date,
            start_time__gte=start_time,
            is_available=True
        ).order_by('start_time')[:required_slots]
        
        if len(available_slots) < required_slots:
            return JsonResponse({
                'error': 'Not enough consecutive time slots available',
                'required_slots': required_slots,
                'available_slots': len(available_slots)
            }, status=400)
            
        # Create the booking
        booking = Booking.objects.create(
            business=business,
            customer=request.user,
            status='pending'
        )
        
        # Add services
        booking.services.set(services)
        
        # Add time slots
        for slot in available_slots:
            booking.time_slots.add(slot)
            slot.is_available = False
            slot.save()
        
        return JsonResponse({
            'message': 'Booking created successfully',
            'booking': {
                'id': booking.id,
                'services': [{
                    'id': service.id,
                    'name': service.name,
                    'duration': service.duration,
                    'price': str(service.price)
                } for service in services],
                'total_duration': total_duration,
                'slots_used': required_slots,
                'date': date_str,
                'start_time': start_time_str,
                'end_time': available_slots.last().end_time.strftime('%H:%M'),
                'status': booking.status
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_available_slots(request):
    """
    Get available slots for a specific date and employee, considering service durations.
    
    Query parameters:
    - business_id: ID of the business
    - employee_id: ID of the employee
    - date: Date in YYYY-MM-DD format
    - service_ids: Comma-separated list of service IDs
    """
    try:
        business_id = request.GET.get('business_id')
        employee_id = request.GET.get('employee_id')
        date_str = request.GET.get('date')
        service_ids = request.GET.get('service_ids', '').split(',')
        
        if not all([business_id, employee_id, date_str, service_ids]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
        # Convert service_ids to integers and remove empty strings
        service_ids = [int(sid) for sid in service_ids if sid]
        
        # Get services and calculate total duration
        services = Service.objects.filter(id__in=service_ids, business_id=business_id)
        total_duration = sum(service.duration for service in services)
        required_slots = (total_duration + 29) // 30  # Round up to nearest 30-min slot
        
        # Parse date
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
            
        # Get employee's shifts for this day
        day_of_week = booking_date.weekday()
        shifts = Shift.objects.filter(
            employee_id=employee_id,
            day_of_week=day_of_week,
            is_active=True
        )
        
        available_slots = []
        
        for shift in shifts:
            # Get all available slots for this shift
            slots = TimeSlot.objects.filter(
                shift=shift,
                date=booking_date,
                is_available=True
            ).order_by('start_time')
            
            # Find consecutive slot groups
            current_group = []
            for slot in slots:
                if not current_group:
                    current_group.append(slot)
                else:
                    # Check if this slot is consecutive with the last one
                    last_slot = current_group[-1]
                    if last_slot.end_time == slot.start_time:
                        current_group.append(slot)
                    else:
                        # If we have enough slots in the current group, add it to available slots
                        if len(current_group) >= required_slots:
                            start_slot = current_group[0]
                            end_slot = current_group[required_slots - 1]
                            available_slots.append({
                                'start_time': start_slot.start_time.strftime('%H:%M'),
                                'end_time': end_slot.end_time.strftime('%H:%M'),
                                'duration': total_duration,
                                'slots_needed': required_slots
                            })
                        current_group = [slot]
                        
            # Check the last group
            if len(current_group) >= required_slots:
                start_slot = current_group[0]
                end_slot = current_group[required_slots - 1]
                available_slots.append({
                    'start_time': start_slot.start_time.strftime('%H:%M'),
                    'end_time': end_slot.end_time.strftime('%H:%M'),
                    'duration': total_duration,
                    'slots_needed': required_slots
                })
        
        return JsonResponse({
            'date': date_str,
            'total_duration': total_duration,
            'slots_needed': required_slots,
            'available_slots': available_slots
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_business_bookings(request):
    """
    Get all bookings for a business with optional filters.
    
    Query parameters:
    - date: Optional date filter (YYYY-MM-DD)
    - status: Optional status filter (pending, confirmed, cancelled, completed)
    - employee_id: Optional employee filter
    - customer_search: Optional customer name/email search
    """
    try:
        # Get the business for the current user
        try:
            business = Business.objects.get(owner=request.user)
        except Business.DoesNotExist:
            return JsonResponse({'error': 'No business found for this user'}, status=404)
        
        # Get query parameters
        date_str = request.GET.get('date')
        status = request.GET.get('status')
        employee_id = request.GET.get('employee_id')
        customer_search = request.GET.get('customer_search')
        
        # Start with all bookings for this business
        bookings = Booking.objects.filter(business=business).select_related(
            'customer'
        ).prefetch_related(
            'services',
            'time_slots',
            'time_slots__shift__employee'
        )
        
        # Apply filters if provided
        if date_str:
            try:
                booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                bookings = bookings.filter(time_slots__date=booking_date).distinct()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        if status:
            bookings = bookings.filter(status=status)
            
        if employee_id:
            bookings = bookings.filter(time_slots__shift__employee_id=employee_id).distinct()
            
        if customer_search:
            bookings = bookings.filter(
                models.Q(customer__username__icontains=customer_search) |
                models.Q(customer__email__icontains=customer_search) |
                models.Q(customer__first_name__icontains=customer_search) |
                models.Q(customer__last_name__icontains=customer_search)
            ).distinct()
        
        # Format the response
        bookings_data = []
        for booking in bookings:
            # Get the first and last time slots to determine overall time range
            time_slots = booking.time_slots.order_by('start_time')
            first_slot = time_slots.first()
            last_slot = time_slots.last()
            
            if first_slot and last_slot:
                booking_data = {
                    'id': booking.id,
                    'customer': {
                        'id': booking.customer.id,
                        'name': f"{booking.customer.first_name} {booking.customer.last_name}".strip() or booking.customer.username,
                        'email': booking.customer.email
                    },
                    'services': [{
                        'id': service.id,
                        'name': service.name,
                        'duration': service.duration,
                        'price': str(service.price)
                    } for service in booking.services.all()],
                    'date': first_slot.date.strftime('%Y-%m-%d'),
                    'start_time': first_slot.start_time.strftime('%H:%M'),
                    'end_time': last_slot.end_time.strftime('%H:%M'),
                    'employee': {
                        'id': first_slot.shift.employee.id,
                        'name': first_slot.shift.employee.name
                    },
                    'total_duration': booking.total_duration,
                    'status': booking.status,
                    'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': booking.notes
                }
                bookings_data.append(booking_data)
        
        return JsonResponse({
            'bookings': bookings_data,
            'total_count': len(bookings_data),
            'filters_applied': {
                'date': date_str,
                'status': status,
                'employee_id': employee_id,
                'customer_search': customer_search
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(type(e).__name__)
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_details(request, employee_id):
    """
    Get detailed information about an employee including their stats
    """
    try:
        business = Business.objects.get(owner=request.user)
        employee = get_object_or_404(Employee, id=employee_id, business=business)
        
        # Get employee's active shifts
        shifts = Shift.objects.filter(employee=employee, is_active=True)
        
        # Get employee's upcoming bookings
        upcoming_bookings = Booking.objects.filter(
            time_slots__shift__employee=employee,
            time_slots__date__gte=datetime.now().date(),
            status__in=['pending', 'confirmed']
        ).distinct()
        
        # Get employee's completed bookings
        completed_bookings = Booking.objects.filter(
            time_slots__shift__employee=employee,
            status='completed'
        ).distinct()
        
        # Calculate statistics
        total_completed = completed_bookings.count()
        total_upcoming = upcoming_bookings.count()
        total_shifts = shifts.count()
        
        # Calculate total slots per week
        weekly_slots = 0
        for shift in shifts:
            duration_minutes = (
                datetime.combine(datetime.min, shift.end_time) - 
                datetime.combine(datetime.min, shift.start_time)
            ).seconds / 60
            weekly_slots += duration_minutes / 30  # 30-minute slots
        
        return JsonResponse({
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'image': employee.image.url if employee.image else None,
                'stats': {
                    'total_completed_bookings': total_completed,
                    'total_upcoming_bookings': total_upcoming,
                    'total_shifts': total_shifts,
                    'weekly_slots': int(weekly_slots),
                }
            }
        })
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_bookings(request, employee_id):
    """
    Get all bookings for a specific employee with optional filters
    """
    try:
        business = Business.objects.get(owner=request.user)
        employee = get_object_or_404(Employee, id=employee_id, business=business)
        
        # Get query parameters
        status = request.GET.get('status', 'upcoming')
        date_from = request.GET.get('dateFrom')
        date_to = request.GET.get('dateTo')
        
        # Start with all bookings for this employee
        bookings = Booking.objects.filter(
            time_slots__shift__employee=employee
        ).distinct().select_related(
            'customer'
        ).prefetch_related(
            'services',
            'time_slots',
            'time_slots__shift'
        )
        
        # Apply filters
        if status != 'all':
            if status == 'upcoming':
                bookings = bookings.filter(
                    time_slots__date__gte=datetime.now().date(),
                    status__in=['pending', 'confirmed']
                )
            else:
                bookings = bookings.filter(status=status)
            
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                bookings = bookings.filter(time_slots__date__gte=date_from)
            except ValueError:
                return JsonResponse({'error': 'Invalid date_from format'}, status=400)
                
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                bookings = bookings.filter(time_slots__date__lte=date_to)
            except ValueError:
                return JsonResponse({'error': 'Invalid date_to format'}, status=400)
        
        # Format response
        bookings_data = []
        for booking in bookings:
            # Get the first and last time slots to determine overall time range
            time_slots = booking.time_slots.order_by('start_time')
            first_slot = time_slots.first()
            last_slot = time_slots.last()
            
            if first_slot and last_slot:
                booking_data = {
                    'id': booking.id,
                    'customer': {
                        'name': booking.customer.get_full_name() or booking.customer.username,
                        'email': booking.customer.email
                    },
                    'services': [{
                        'name': service.name,
                        'duration': service.duration
                    } for service in booking.services.all()],
                    'date': first_slot.date.strftime('%Y-%m-%d'),
                    'start_time': first_slot.start_time.strftime('%H:%M'),
                    'end_time': last_slot.end_time.strftime('%H:%M'),
                    'status': booking.status,
                    'total_duration': sum(service.duration for service in booking.services.all())
                }
                bookings_data.append(booking_data)
        
        return JsonResponse({
            'bookings': bookings_data,
            'total': len(bookings_data),
            'filters': {
                'status': status,
                'dateFrom': date_from.strftime('%Y-%m-%d') if date_from else None,
                'dateTo': date_to.strftime('%Y-%m-%d') if date_to else None
            }
        })
        
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_shifts(request, employee_id):
    """
    Get all shifts for a specific employee
    """
    try:
        business = Business.objects.get(owner=request.user)
        employee = get_object_or_404(Employee, id=employee_id, business=business)
        
        # Get all active shifts for this employee
        shifts = Shift.objects.filter(
            employee=employee,
            is_active=True
        )
        
        # Organize shifts by day
        weekly_shifts = {
            'Monday': [], 'Tuesday': [], 'Wednesday': [], 
            'Thursday': [], 'Friday': [], 'Saturday': [], 'Sunday': []
        }
        
        for shift in shifts:
            day = shift.get_day_of_week_display()
            slots = (
                datetime.combine(datetime.min, shift.end_time) - 
                datetime.combine(datetime.min, shift.start_time)
            ).seconds / 1800  # 1800 seconds = 30 minutes
            
            weekly_shifts[day].append({
                'id': shift.id,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'slots': int(slots)
            })
        
        return JsonResponse({
            'weekly_shifts': weekly_shifts
        })
        
    except Business.DoesNotExist:
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
