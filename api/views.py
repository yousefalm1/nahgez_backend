from django.shortcuts import render

# Create your views here.
from ninja import NinjaAPI, Schema
from typing import List, Optional, Dict
from businesses.models import Business, Service, Employee, Booking, Shift, TimeSlot
from datetime import datetime, date, timedelta
from pydantic import Field
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth.models import User

api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return {"message": "Hello from Nahjez API"}

# Define schemas for the API responses
class ServiceSchema(Schema):
    id: int
    name: str
    description: str
    price: float
    duration: int
    is_active: bool

class EmployeeSchema(Schema):
    id: int
    name: str
    image: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    services: List[int] = []  # List of service IDs

class BusinessSchema(Schema):
    id: int
    name: str
    description: str
    main_image: Optional[str] = None
    image1: Optional[str] = None
    image2: Optional[str] = None
    image3: Optional[str] = None
    image4: Optional[str] = None
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: str
    email: str
    opening_hours: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    services: List[ServiceSchema] = []
    employees: List[EmployeeSchema] = []

@api.get("/businesses", response=List[BusinessSchema])
def get_businesses(request):
    """
    Get all businesses with their details including services and employees
    """
    businesses = Business.objects.filter(is_active=True)
    result = []
    
    for business in businesses:
        # Get services for this business
        services = [
            ServiceSchema(
                id=service.id,
                name=service.name,
                description=service.description,
                price=float(service.price),
                duration=service.duration,
                is_active=service.is_active
            )
            for service in business.services.filter(is_active=True)
        ]
        
        # Get employees for this business
        employees = []
        for employee in business.employees.filter(is_active=True):
            # Safely get image URL
            image_url = None
            if employee.image and employee.image.name:
                try:
                    image_url = employee.image.url
                except ValueError:
                    image_url = None
                    
            employee_data = EmployeeSchema(
                id=employee.id,
                name=employee.name,
                image=image_url,
                phone=employee.phone,
                email=employee.email,
                is_active=employee.is_active,
                services=[service.id for service in employee.services.all()]
            )
            employees.append(employee_data)
        
        # Safely get image URLs
        main_image_url = None
        if business.main_image and business.main_image.name:
            try:
                main_image_url = business.main_image.url
            except ValueError:
                main_image_url = None
                
        image1_url = None
        if business.image1 and business.image1.name:
            try:
                image1_url = business.image1.url
            except ValueError:
                image1_url = None
                
        image2_url = None
        if business.image2 and business.image2.name:
            try:
                image2_url = business.image2.url
            except ValueError:
                image2_url = None
                
        image3_url = None
        if business.image3 and business.image3.name:
            try:
                image3_url = business.image3.url
            except ValueError:
                image3_url = None
                
        image4_url = None
        if business.image4 and business.image4.name:
            try:
                image4_url = business.image4.url
            except ValueError:
                image4_url = None
        
        # Create business data
        business_data = BusinessSchema(
            id=business.id,
            name=business.name,
            description=business.description,
            main_image=main_image_url,
            image1=image1_url,
            image2=image2_url,
            image3=image3_url,
            image4=image4_url,
            address=business.address,
            latitude=float(business.latitude) if business.latitude else None,
            longitude=float(business.longitude) if business.longitude else None,
            phone=business.phone,
            email=business.email,
            opening_hours=business.opening_hours,
            is_active=business.is_active,
            created_at=business.created_at,
            updated_at=business.updated_at,
            services=services,
            employees=employees
        )
        
        result.append(business_data)
    
    return result

@api.get("/businesses/{business_id}", response=BusinessSchema)
def get_business(request, business_id: int):
    """
    Get a specific business by ID with all its details
    """
    try:
        business = Business.objects.get(id=business_id, is_active=True)
    except Business.DoesNotExist:
        return api.create_response(request, {"message": "Business not found"}, status=404)
    
    # Get services for this business
    services = [
        ServiceSchema(
            id=service.id,
            name=service.name,
            description=service.description,
            price=float(service.price),
            duration=service.duration,
            is_active=service.is_active
        )
        for service in business.services.filter(is_active=True)
    ]
    
    # Get employees for this business
    employees = []
    for employee in business.employees.filter(is_active=True):
        # Safely get image URL
        image_url = None
        if employee.image and employee.image.name:
            try:
                image_url = employee.image.url
            except ValueError:
                image_url = None
                
        employee_data = EmployeeSchema(
            id=employee.id,
            name=employee.name,
            image=image_url,
            phone=employee.phone,
            email=employee.email,
            is_active=employee.is_active,
            services=[service.id for service in employee.services.all()]
        )
        employees.append(employee_data)
    
    # Safely get image URLs
    main_image_url = None
    if business.main_image and business.main_image.name:
        try:
            main_image_url = business.main_image.url
        except ValueError:
            main_image_url = None
            
    image1_url = None
    if business.image1 and business.image1.name:
        try:
            image1_url = business.image1.url
        except ValueError:
            image1_url = None
            
    image2_url = None
    if business.image2 and business.image2.name:
        try:
            image2_url = business.image2.url
        except ValueError:
            image2_url = None
            
    image3_url = None
    if business.image3 and business.image3.name:
        try:
            image3_url = business.image3.url
        except ValueError:
            image3_url = None
            
    image4_url = None
    if business.image4 and business.image4.name:
        try:
            image4_url = business.image4.url
        except ValueError:
            image4_url = None
    
    # Create business data
    business_data = BusinessSchema(
        id=business.id,
        name=business.name,
        description=business.description,
        main_image=main_image_url,
        image1=image1_url,
        image2=image2_url,
        image3=image3_url,
        image4=image4_url,
        address=business.address,
        latitude=float(business.latitude) if business.latitude else None,
        longitude=float(business.longitude) if business.longitude else None,
        phone=business.phone,
        email=business.email,
        opening_hours=business.opening_hours,
        is_active=business.is_active,
        created_at=business.created_at,
        updated_at=business.updated_at,
        services=services,
        employees=employees
    )
    
    return business_data

# Schemas for the booking system
class ShiftSchema(Schema):
    id: int
    shift_type: str
    day_of_week: Optional[int] = None
    specific_date: Optional[date] = None
    start_time: str
    end_time: str
    is_active: bool
    employee_id: int
    business_id: int

class TimeSlotSchema(Schema):
    id: int
    date: date
    start_time: str
    end_time: str
    is_available: bool
    shift_id: int
    employee_id: int
    business_id: int

class BookingCreateSchema(Schema):
    time_slot_id: int
    service_id: int
    notes: Optional[str] = None

class BookingResponseSchema(Schema):
    id: int
    customer_id: int
    business_id: int
    service_id: int
    time_slot: TimeSlotSchema
    status: str
    notes: Optional[str] = None
    created_at: datetime

class ShiftCreateSchema(Schema):
    employee_id: int
    shift_type: str = 'recurring'
    day_of_week: Optional[int] = None
    specific_date: Optional[date] = None
    start_time: str
    end_time: str
    is_active: bool = True

# Endpoints for barbershop owners

@api.post("/businesses/{business_id}/shifts", response=ShiftSchema)
def create_shift(request, business_id: int, shift_data: ShiftCreateSchema):
    """Create a new shift for an employee"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    business = get_object_or_404(Business, id=business_id)
    
    # Check if the user is the owner of the business
    if business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    employee = get_object_or_404(Employee, id=shift_data.employee_id, business=business)
    
    # Validate shift data
    if shift_data.shift_type == 'recurring' and shift_data.day_of_week is None:
        return api.create_response(request, {"detail": "Day of week is required for recurring shifts"}, status=400)
    
    if shift_data.shift_type == 'one_time' and shift_data.specific_date is None:
        return api.create_response(request, {"detail": "Specific date is required for one-time shifts"}, status=400)
    
    # Create the shift
    shift = Shift.objects.create(
        business=business,
        employee=employee,
        shift_type=shift_data.shift_type,
        day_of_week=shift_data.day_of_week,
        specific_date=shift_data.specific_date,
        start_time=shift_data.start_time,
        end_time=shift_data.end_time,
        is_active=shift_data.is_active
    )
    
    return {
        "id": shift.id,
        "shift_type": shift.shift_type,
        "day_of_week": shift.day_of_week,
        "specific_date": shift.specific_date,
        "start_time": shift.start_time.strftime("%H:%M"),
        "end_time": shift.end_time.strftime("%H:%M"),
        "is_active": shift.is_active,
        "employee_id": employee.id,
        "business_id": business.id
    }

@api.get("/businesses/{business_id}/shifts", response=List[ShiftSchema])
def get_shifts(request, business_id: int, shift_type: Optional[str] = None, employee_id: Optional[int] = None):
    """Get all shifts for a business with optional filtering"""
    business = get_object_or_404(Business, id=business_id)
    
    # Build the query
    query = Q(business=business)
    
    if shift_type:
        query &= Q(shift_type=shift_type)
    
    if employee_id:
        query &= Q(employee_id=employee_id)
    
    shifts = Shift.objects.filter(query)
    
    result = []
    for shift in shifts:
        result.append({
            "id": shift.id,
            "shift_type": shift.shift_type,
            "day_of_week": shift.day_of_week,
            "specific_date": shift.specific_date,
            "start_time": shift.start_time.strftime("%H:%M"),
            "end_time": shift.end_time.strftime("%H:%M"),
            "is_active": shift.is_active,
            "employee_id": shift.employee.id,
            "business_id": business.id
        })
    
    return result

@api.put("/shifts/{shift_id}", response=ShiftSchema)
def update_shift(request, shift_id: int, shift_data: ShiftCreateSchema):
    """Update a shift"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    shift = get_object_or_404(Shift, id=shift_id)
    
    # Check if the user is the owner of the business
    if shift.business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Validate shift data
    if shift_data.shift_type == 'recurring' and shift_data.day_of_week is None:
        return api.create_response(request, {"detail": "Day of week is required for recurring shifts"}, status=400)
    
    if shift_data.shift_type == 'one_time' and shift_data.specific_date is None:
        return api.create_response(request, {"detail": "Specific date is required for one-time shifts"}, status=400)
    
    # Update the shift
    shift.shift_type = shift_data.shift_type
    shift.day_of_week = shift_data.day_of_week
    shift.specific_date = shift_data.specific_date
    shift.start_time = shift_data.start_time
    shift.end_time = shift_data.end_time
    shift.is_active = shift_data.is_active
    shift.save()
    
    return {
        "id": shift.id,
        "shift_type": shift.shift_type,
        "day_of_week": shift.day_of_week,
        "specific_date": shift.specific_date,
        "start_time": shift.start_time.strftime("%H:%M"),
        "end_time": shift.end_time.strftime("%H:%M"),
        "is_active": shift.is_active,
        "employee_id": shift.employee.id,
        "business_id": shift.business.id
    }

@api.delete("/shifts/{shift_id}")
def delete_shift(request, shift_id: int):
    """Delete a shift"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    shift = get_object_or_404(Shift, id=shift_id)
    
    # Check if the user is the owner of the business
    if shift.business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Delete the shift
    shift.delete()
    
    return {"success": True}

@api.post("/shifts/{shift_id}/generate-slots")
def generate_time_slots(request, shift_id: int, days_ahead: int = 7):
    """Generate time slots for a shift for the next X days"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    shift = get_object_or_404(Shift, id=shift_id)
    
    # Check if the user is the owner of the business
    if shift.business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Generate time slots for the next X days
    today = datetime.now().date()
    slots_created = 0
    
    for i in range(days_ahead):
        target_date = today + timedelta(days=i)
        # Only generate slots if the day of week matches
        if target_date.weekday() == shift.day_of_week:
            slots = shift.generate_time_slots(date=target_date)
            slots_created += len(slots)
    
    return {"slots_created": slots_created}

@api.post("/businesses/{business_id}/generate-slots")
def generate_business_time_slots(request, business_id: int, days_ahead: int = 7, slot_duration: int = 30):
    """Generate time slots for all employees in a business for the next X days"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    business = get_object_or_404(Business, id=business_id)
    
    # Check if the user is the owner of the business
    if business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Generate time slots for all employees
    result = business.generate_all_time_slots(days=days_ahead, slot_duration=slot_duration)
    
    # Calculate total slots created
    total_slots = sum(result.values())
    
    return {
        "total_slots_created": total_slots,
        "per_employee": result
    }

# Endpoints for customers

@api.get("/businesses/{business_id}/available-slots", response=List[TimeSlotSchema])
def get_available_slots(request, business_id: int, date_from: Optional[date] = None, date_to: Optional[date] = None, employee_id: Optional[int] = None):
    """Get available time slots for a business"""
    business = get_object_or_404(Business, id=business_id)
    
    # Default to next 7 days if not specified
    if date_from is None:
        date_from = datetime.now().date()
    if date_to is None:
        date_to = date_from + timedelta(days=7)
    
    # Build the query
    query = Q(
        shift__business=business,
        date__gte=date_from,
        date__lte=date_to,
        is_available=True
    )
    
    # Filter by employee if specified
    if employee_id:
        query &= Q(shift__employee_id=employee_id)
    
    # Get the available slots
    slots = TimeSlot.objects.filter(query).order_by('date', 'start_time')
    
    result = []
    for slot in slots:
        result.append({
            "id": slot.id,
            "date": slot.date,
            "start_time": slot.start_time.strftime("%H:%M"),
            "end_time": slot.end_time.strftime("%H:%M"),
            "is_available": slot.is_available,
            "shift_id": slot.shift.id,
            "employee_id": slot.shift.employee.id,
            "business_id": slot.shift.business.id
        })
    
    return result

@api.post("/bookings", response=BookingResponseSchema)
def create_booking(request, booking_data: BookingCreateSchema):
    """Create a new booking"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Get the time slot
    time_slot = get_object_or_404(TimeSlot, id=booking_data.time_slot_id)
    
    # Check if the slot is available
    if not time_slot.is_available:
        return api.create_response(request, {"detail": "Time slot is not available"}, status=400)
    
    # Get the service
    service = get_object_or_404(Service, id=booking_data.service_id)
    
    # Check if the service belongs to the business
    if service.business != time_slot.shift.business:
        return api.create_response(request, {"detail": "Service does not belong to this business"}, status=400)
    
    # Check if the employee provides this service
    if service not in time_slot.shift.employee.services.all():
        return api.create_response(request, {"detail": "Employee does not provide this service"}, status=400)
    
    # Create the booking
    booking = Booking.objects.create(
        business=time_slot.shift.business,
        customer=request.user,
        service=service,
        time_slot=time_slot,
        notes=booking_data.notes
    )
    
    # The time_slot is marked as unavailable in the Booking.save() method
    
    return {
        "id": booking.id,
        "customer_id": booking.customer.id,
        "business_id": booking.business.id,
        "service_id": booking.service.id,
        "time_slot": {
            "id": time_slot.id,
            "date": time_slot.date,
            "start_time": time_slot.start_time.strftime("%H:%M"),
            "end_time": time_slot.end_time.strftime("%H:%M"),
            "is_available": time_slot.is_available,
            "shift_id": time_slot.shift.id,
            "employee_id": time_slot.shift.employee.id,
            "business_id": time_slot.shift.business.id
        },
        "status": booking.status,
        "notes": booking.notes,
        "created_at": booking.created_at
    }

@api.get("/bookings/{booking_id}", response=BookingResponseSchema)
def get_booking(request, booking_id: int):
    """Get a booking by ID"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Get the booking
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if the user is authorized to view this booking
    if booking.customer != request.user and booking.business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Handle legacy bookings that don't have a time_slot
    if not booking.time_slot:
        # For legacy bookings, we'll return a simplified response
        return {
            "id": booking.id,
            "customer_id": booking.customer.id,
            "business_id": booking.business.id,
            "service_id": booking.service.id,
            "time_slot": {
                "id": 0,  # Placeholder ID
                "date": booking.date or datetime.now().date(),
                "start_time": booking.time.strftime("%H:%M") if booking.time else "00:00",
                "end_time": "00:00",  # Placeholder
                "is_available": False,
                "shift_id": 0,  # Placeholder ID
                "employee_id": booking.employee.id if booking.employee else 0,
                "business_id": booking.business.id
            },
            "status": booking.status,
            "notes": booking.notes,
            "created_at": booking.created_at
        }
    
    time_slot = booking.time_slot
    
    return {
        "id": booking.id,
        "customer_id": booking.customer.id,
        "business_id": booking.business.id,
        "service_id": booking.service.id,
        "time_slot": {
            "id": time_slot.id,
            "date": time_slot.date,
            "start_time": time_slot.start_time.strftime("%H:%M"),
            "end_time": time_slot.end_time.strftime("%H:%M"),
            "is_available": time_slot.is_available,
            "shift_id": time_slot.shift.id,
            "employee_id": time_slot.shift.employee.id,
            "business_id": time_slot.shift.business.id
        },
        "status": booking.status,
        "notes": booking.notes,
        "created_at": booking.created_at
    }

@api.put("/bookings/{booking_id}/cancel")
def cancel_booking(request, booking_id: int):
    """Cancel a booking"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Get the booking
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if the user is authorized to cancel this booking
    if booking.customer != request.user and booking.business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Check if the booking can be cancelled
    if booking.status == 'cancelled':
        return api.create_response(request, {"detail": "Booking is already cancelled"}, status=400)
    
    if booking.status == 'completed':
        return api.create_response(request, {"detail": "Completed bookings cannot be cancelled"}, status=400)
    
    # Cancel the booking
    booking.status = 'cancelled'
    booking.save()  # This will also make the time slot available again
    
    return {"success": True}

@api.get("/my-bookings", response=List[BookingResponseSchema])
def get_my_bookings(request):
    """Get all bookings for the current user"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Get the bookings
    bookings = Booking.objects.filter(customer=request.user).order_by('-created_at')
    
    result = []
    for booking in bookings:
        # Handle legacy bookings that don't have a time_slot
        if not booking.time_slot:
            result.append({
                "id": booking.id,
                "customer_id": booking.customer.id,
                "business_id": booking.business.id,
                "service_id": booking.service.id,
                "time_slot": {
                    "id": 0,  # Placeholder ID
                    "date": booking.date or datetime.now().date(),
                    "start_time": booking.time.strftime("%H:%M") if booking.time else "00:00",
                    "end_time": "00:00",  # Placeholder
                    "is_available": False,
                    "shift_id": 0,  # Placeholder ID
                    "employee_id": booking.employee.id if booking.employee else 0,
                    "business_id": booking.business.id
                },
                "status": booking.status,
                "notes": booking.notes,
                "created_at": booking.created_at
            })
            continue
            
        time_slot = booking.time_slot
        result.append({
            "id": booking.id,
            "customer_id": booking.customer.id,
            "business_id": booking.business.id,
            "service_id": booking.service.id,
            "time_slot": {
                "id": time_slot.id,
                "date": time_slot.date,
                "start_time": time_slot.start_time.strftime("%H:%M"),
                "end_time": time_slot.end_time.strftime("%H:%M"),
                "is_available": time_slot.is_available,
                "shift_id": time_slot.shift.id,
                "employee_id": time_slot.shift.employee.id,
                "business_id": time_slot.shift.business.id
            },
            "status": booking.status,
            "notes": booking.notes,
            "created_at": booking.created_at
        })
    
    return result

@api.get("/businesses/{business_id}/bookings", response=List[BookingResponseSchema])
def get_business_bookings(request, business_id: int):
    """Get all bookings for a business"""
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    business = get_object_or_404(Business, id=business_id)
    
    # Check if the user is the owner of the business
    if business.owner != request.user:
        return api.create_response(request, {"detail": "Not authorized"}, status=403)
    
    # Get the bookings
    bookings = Booking.objects.filter(business=business).order_by('-created_at')
    
    result = []
    for booking in bookings:
        # Handle legacy bookings that don't have a time_slot
        if not booking.time_slot:
            result.append({
                "id": booking.id,
                "customer_id": booking.customer.id,
                "business_id": booking.business.id,
                "service_id": booking.service.id,
                "time_slot": {
                    "id": 0,  # Placeholder ID
                    "date": booking.date or datetime.now().date(),
                    "start_time": booking.time.strftime("%H:%M") if booking.time else "00:00",
                    "end_time": "00:00",  # Placeholder
                    "is_available": False,
                    "shift_id": 0,  # Placeholder ID
                    "employee_id": booking.employee.id if booking.employee else 0,
                    "business_id": booking.business.id
                },
                "status": booking.status,
                "notes": booking.notes,
                "created_at": booking.created_at
            })
            continue
            
        time_slot = booking.time_slot
        result.append({
            "id": booking.id,
            "customer_id": booking.customer.id,
            "business_id": booking.business.id,
            "service_id": booking.service.id,
            "time_slot": {
                "id": time_slot.id,
                "date": time_slot.date,
                "start_time": time_slot.start_time.strftime("%H:%M"),
                "end_time": time_slot.end_time.strftime("%H:%M"),
                "is_available": time_slot.is_available,
                "shift_id": time_slot.shift.id,
                "employee_id": time_slot.shift.employee.id,
                "business_id": time_slot.shift.business.id
            },
            "status": booking.status,
            "notes": booking.notes,
            "created_at": booking.created_at
        })
    
    return result

@api.get("/my-business/schedule", response=List[ShiftSchema])
def get_my_business_schedule(request, date_from: Optional[date] = None, date_to: Optional[date] = None):
    """
    Get the schedule for the authenticated business owner's business.
    This endpoint requires authentication with a bearer token.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Check if user is a business owner
    if not request.user.groups.filter(name='Business Owners').exists():
        return api.create_response(request, {"detail": "You must be a business owner to access this endpoint"}, status=403)
    
    # Get the business for the authenticated user
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return api.create_response(request, {"detail": "No business found for this user"}, status=404)
    
    # Set default date range if not provided
    if not date_from:
        date_from = datetime.now().date()
    if not date_to:
        date_to = date_from + timedelta(days=30)  # Default to 30 days ahead
    
    # Get all shifts for the business within the date range
    shifts = Shift.objects.filter(business=business, is_active=True)
    
    result = []
    for shift in shifts:
        # For recurring shifts, check if they occur within the date range
        if shift.shift_type == 'recurring':
            # Add the shift if it occurs on a day within the date range
            current_date = date_from
            while current_date <= date_to:
                if current_date.weekday() == shift.day_of_week:
                    result.append({
                        "id": shift.id,
                        "shift_type": shift.shift_type,
                        "day_of_week": shift.day_of_week,
                        "specific_date": current_date,  # Use the actual date for this occurrence
                        "start_time": shift.start_time.strftime("%H:%M"),
                        "end_time": shift.end_time.strftime("%H:%M"),
                        "is_active": shift.is_active,
                        "employee_id": shift.employee.id,
                        "business_id": business.id
                    })
                current_date += timedelta(days=1)
        # For one-time shifts, add them if they fall within the date range
        elif shift.shift_type == 'one_time' and shift.specific_date and date_from <= shift.specific_date <= date_to:
            result.append({
                "id": shift.id,
                "shift_type": shift.shift_type,
                "day_of_week": None,
                "specific_date": shift.specific_date,
                "start_time": shift.start_time.strftime("%H:%M"),
                "end_time": shift.end_time.strftime("%H:%M"),
                "is_active": shift.is_active,
                "employee_id": shift.employee.id,
                "business_id": business.id
            })
    
    return result

@api.get("/my-business/time-slots", response=List[TimeSlotSchema])
def get_my_business_time_slots(request, date_from: Optional[date] = None, date_to: Optional[date] = None):
    """
    Get all time slots for the authenticated business owner's business.
    This endpoint requires authentication with a bearer token.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Check if user is a business owner
    if not request.user.groups.filter(name='Business Owners').exists():
        return api.create_response(request, {"detail": "You must be a business owner to access this endpoint"}, status=403)
    
    # Get the business for the authenticated user
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return api.create_response(request, {"detail": "No business found for this user"}, status=404)
    
    # Set default date range if not provided
    if not date_from:
        date_from = datetime.now().date()
    if not date_to:
        date_to = date_from + timedelta(days=7)  # Default to a week ahead
    
    # Get all time slots for the business within the date range
    time_slots = TimeSlot.objects.filter(
        shift__business=business,
        date__gte=date_from,
        date__lte=date_to
    ).select_related('shift', 'shift__employee')
    
    result = []
    for slot in time_slots:
        result.append({
            "id": slot.id,
            "date": slot.date,
            "start_time": slot.start_time.strftime("%H:%M"),
            "end_time": slot.end_time.strftime("%H:%M"),
            "is_available": slot.is_available,
            "shift_id": slot.shift.id,
            "employee_id": slot.shift.employee.id,
            "business_id": business.id
        })
    
    return result

@api.get("/my-business/employees", response=List[EmployeeSchema])
def get_my_business_employees(request):
    """
    Get all employees for the authenticated business owner's business.
    This endpoint requires authentication with a bearer token.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Check if user is a business owner
    if not request.user.groups.filter(name='Business Owners').exists():
        return api.create_response(request, {"detail": "You must be a business owner to access this endpoint"}, status=403)
    
    # Get the business for the authenticated user
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return api.create_response(request, {"detail": "No business found for this user"}, status=404)
    
    # Get all employees for the business
    employees = Employee.objects.filter(business=business)
    
    result = []
    for employee in employees:
        result.append({
            "id": employee.id,
            "name": employee.name,
            "image": employee.image.url if employee.image else None,
            "phone": employee.phone,
            "email": employee.email,
            "is_active": employee.is_active,
            "services": [service.id for service in employee.services.all()]
        })
    
    return result

@api.get("/my-business/bookings", response=List[BookingResponseSchema])
def get_my_business_bookings(request):
    """
    Get all bookings for the authenticated business owner's business.
    This endpoint requires authentication with a bearer token.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Check if user is a business owner
    if not request.user.groups.filter(name='Business Owners').exists():
        return api.create_response(request, {"detail": "You must be a business owner to access this endpoint"}, status=403)
    
    # Get the business for the authenticated user
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return api.create_response(request, {"detail": "No business found for this user"}, status=404)
    
    # Get all bookings for the business
    bookings = Booking.objects.filter(business=business).select_related('time_slot', 'service', 'customer')
    
    result = []
    for booking in bookings:
        # Skip bookings without a time slot (legacy bookings)
        if not booking.time_slot:
            continue
            
        time_slot = booking.time_slot
        result.append({
            "id": booking.id,
            "customer_id": booking.customer.id,
            "business_id": business.id,
            "service_id": booking.service.id,
            "time_slot": {
                "id": time_slot.id,
                "date": time_slot.date,
                "start_time": time_slot.start_time.strftime("%H:%M"),
                "end_time": time_slot.end_time.strftime("%H:%M"),
                "is_available": time_slot.is_available,
                "shift_id": time_slot.shift.id,
                "employee_id": time_slot.shift.employee.id,
                "business_id": business.id
            },
            "status": booking.status,
            "notes": booking.notes,
            "created_at": booking.created_at
        })
    
    return result

@api.post("/my-business/generate-slots")
def generate_my_business_time_slots(request, days_ahead: int = 7, slot_duration: int = 30):
    """
    Generate time slots for all employees in the authenticated business owner's business.
    This endpoint requires authentication with a bearer token.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return api.create_response(request, {"detail": "Authentication required"}, status=401)
    
    # Check if user is a business owner
    if not request.user.groups.filter(name='Business Owners').exists():
        return api.create_response(request, {"detail": "You must be a business owner to access this endpoint"}, status=403)
    
    # Get the business for the authenticated user
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return api.create_response(request, {"detail": "No business found for this user"}, status=404)
    
    # Generate time slots for all employees
    result = business.generate_all_time_slots(days=days_ahead, slot_duration=slot_duration)
    
    # Calculate total slots created
    total_slots = sum(result.values())
    
    return {
        "total_slots_created": total_slots,
        "per_employee": result
    }