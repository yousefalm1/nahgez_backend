from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, time

class Business(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Images
    main_image = models.ImageField(upload_to='business/main/')
    image1 = models.ImageField(upload_to='business/gallery/', blank=True, null=True)
    image2 = models.ImageField(upload_to='business/gallery/', blank=True, null=True)
    image3 = models.ImageField(upload_to='business/gallery/', blank=True, null=True)
    image4 = models.ImageField(upload_to='business/gallery/', blank=True, null=True)
    
    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Business Hours
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    
    opening_hours = models.JSONField(default=dict, help_text="""
    Format: {
        "0": {"open": "09:00", "close": "18:00"},
        "1": {"open": "09:00", "close": "18:00"},
        ...
    }
    """)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        app_label = "businesses"
        
    def generate_all_time_slots(self, days=7, slot_duration=30):
        """
        Generate time slots for all employees for the next X days.
        
        Args:
            days: Number of days to generate slots for
            slot_duration: Duration of each slot in minutes
            
        Returns:
            Dictionary with employee names and number of slots created
        """
        result = {}
        
        # Get all active employees
        employees = self.employees.filter(is_active=True)
        
        for employee in employees:
            slots_created = employee.generate_time_slots_for_next_days(days=days, slot_duration=slot_duration)
            result[employee.name] = slots_created
        
        return result

class Service(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.business.name}"
        
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        app_label = "businesses"

class Employee(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='employees/', blank=True, null=True)
    services = models.ManyToManyField(Service, related_name='employees')
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.business.name}"
        
    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        app_label = "businesses"
        
    def create_weekly_schedule(self, shifts_data):
        """
        Create a weekly schedule for this employee.
        
        Args:
            shifts_data: List of dictionaries with day_of_week, start_time, end_time
            
        Returns:
            List of created Shift objects
        """
        created_shifts = []
        
        # Delete existing shifts
        Shift.objects.filter(employee=self).delete()
        
        # Create new shifts
        for shift_data in shifts_data:
            shift = Shift.objects.create(
                business=self.business,
                employee=self,
                day_of_week=shift_data['day_of_week'],
                start_time=shift_data['start_time'],
                end_time=shift_data['end_time'],
                is_active=shift_data.get('is_active', True)
            )
            created_shifts.append(shift)
        
        return created_shifts
    
    def generate_time_slots_for_next_days(self, days=7, slot_duration=30):
        """
        Generate time slots for this employee for the next X days.
        
        Args:
            days: Number of days to generate slots for
            slot_duration: Duration of each slot in minutes
            
        Returns:
            Number of slots created
        """
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        slots_created = 0
        
        # Get all shifts for this employee
        shifts = Shift.objects.filter(employee=self, is_active=True)
        
        for i in range(days):
            target_date = today + timedelta(days=i)
            day_of_week = target_date.weekday()
            
            # Find shifts for this day of week
            day_shifts = shifts.filter(day_of_week=day_of_week)
            
            # Generate slots for each shift
            for shift in day_shifts:
                slots = shift.generate_time_slots(slot_duration=slot_duration, date=target_date)
                slots_created += len(slots)
        
        return slots_created

class Shift(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='shifts')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shifts')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, default=0)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'day_of_week', 'start_time', 'end_time'],
                name='unique_employee_shift'
            )
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_day_of_week_display()} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
        
    def generate_time_slots(self, slot_duration=30, date=None):
        """
        Generate time slots for this shift.
        
        Args:
            slot_duration: Duration of each slot in minutes (default: 30)
            date: The specific date to generate slots for (required)
            
        Returns:
            List of created TimeSlot objects
        """
        from datetime import datetime, timedelta
        
        if not date:
            raise ValueError("Date is required to generate time slots")
            
        # Delete existing slots for this shift and date
        TimeSlot.objects.filter(shift=self, date=date).delete()
        
        created_slots = []
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        
        while current_time + timedelta(minutes=slot_duration) <= end_time:
            slot = TimeSlot.objects.create(
                shift=self,
                date=date,
                start_time=current_time.time(),
                end_time=(current_time + timedelta(minutes=slot_duration)).time(),
                is_available=True
            )
            created_slots.append(slot)
            current_time += timedelta(minutes=slot_duration)
            
        return created_slots
        
    def save(self, *args, **kwargs):
        """Override save to automatically generate time slots for the next 7 days"""
        is_new = self._state.adding  # Check if this is a new shift
        super().save(*args, **kwargs)
        
        if is_new or kwargs.get('force_generate_slots', False):
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            # Generate slots for the next 7 days
            for i in range(7):
                target_date = today + timedelta(days=i)
                if target_date.weekday() == self.day_of_week:
                    self.generate_time_slots(date=target_date)

class TimeSlot(models.Model):
    """
    Represents a bookable time slot within a shift.
    """
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"
        app_label = "businesses"
        ordering = ['date', 'start_time']
        # Ensure no overlapping slots for the same shift on the same date
        constraints = [
            models.UniqueConstraint(
                fields=['shift', 'date', 'start_time'],
                name='unique_shift_timeslot'
            )
        ]
    
    def __str__(self):
        return f"{self.shift.employee.name} - {self.date} {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"
    
    @property
    def employee(self):
        return self.shift.employee
    
    @property
    def business(self):
        return self.shift.business

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    services = models.ManyToManyField(Service, related_name='bookings')
    
    # Legacy fields (to be removed after migration)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    
    # New fields for multiple time slots
    time_slots = models.ManyToManyField(TimeSlot, related_name='bookings')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.time_slots.exists():
            first_slot = self.time_slots.order_by('start_time').first()
            return f"{self.customer.username} - Multiple Services - {first_slot.date}"
        elif self.date:
            return f"{self.customer.username} - Multiple Services - {self.date}"
        else:
            return f"{self.customer.username} - Multiple Services"
    
    @property
    def total_duration(self):
        """Calculate total duration of all services"""
        return sum(service.duration for service in self.services.all())
    
    @property
    def required_slots(self):
        """Calculate number of 30-minute slots needed"""
        return (self.total_duration + 29) // 30  # Rounds up to nearest slot
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new or kwargs.get('update_slots', False):
            # If this is a new booking or slots need updating
            self._handle_time_slots()
    
    def _handle_time_slots(self):
        """Handle the booking's time slots based on services duration"""
        if not self.time_slots.exists():
            return
        
        required_slots = self.required_slots
        current_slots = list(self.time_slots.order_by('start_time'))
        
        # If we have the wrong number of slots
        if len(current_slots) != required_slots:
            # Start with the first slot
            first_slot = current_slots[0]
            shift = first_slot.shift
            date = first_slot.date
            
            # Get all available consecutive slots from this point
            available_slots = TimeSlot.objects.filter(
                shift=shift,
                date=date,
                start_time__gte=first_slot.start_time,
                is_available=True
            ).order_by('start_time')[:required_slots]
            
            # Verify we have enough consecutive slots
            if len(available_slots) < required_slots:
                raise ValueError("Not enough consecutive time slots available")
            
            # Clear existing slots
            self.time_slots.clear()
            
            # Add new slots and mark them as unavailable
            for slot in available_slots:
                self.time_slots.add(slot)
                slot.is_available = False
                slot.save()
    
    def cancel(self):
        """Cancel the booking and free up the slots"""
        if self.status != 'cancelled':
            self.status = 'cancelled'
            # Make all slots available again
            for slot in self.time_slots.all():
                slot.is_available = True
                slot.save()
            self.save()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        app_label = "businesses"

class BusinessRequest(models.Model):
    BUSINESS_TYPES = [
        ('barbershop', 'Barbershop'),
        ('salon', 'Beauty Salon'),
        ('spa', 'Spa & Wellness'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('more_info', 'More Information Needed')
    ]
    
    # Basic Information
    business_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    description = models.TextField(help_text="Tell us about your business")
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True, null=True, help_text="WhatsApp number (optional)")
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    
    # Social Media
    instagram = models.CharField(max_length=255, blank=True, null=True, help_text="Instagram handle (optional)")
    facebook = models.CharField(max_length=255, blank=True, null=True, help_text="Facebook page URL (optional)")
    website = models.URLField(blank=True, null=True, help_text="Business website (optional)")
    
    # Business Details
    years_in_business = models.PositiveIntegerField(help_text="How many years has your business been operating?")
    number_of_employees = models.PositiveIntegerField(help_text="How many employees do you have?")
    services_offered = models.TextField(help_text="List your main services")
    
    # Additional Information
    has_business_license = models.BooleanField(default=False, help_text="Do you have a valid business license?")
    business_license_number = models.CharField(max_length=100, blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True, help_text="Any additional information you'd like to share")
    
    # Request Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for administrators")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business_name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Business Request"
        verbose_name_plural = "Business Requests"
        ordering = ['-created_at']
