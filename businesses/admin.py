from django.contrib import admin
from django.contrib.auth.models import User
from .models import Business, Service, Employee, Booking, BusinessRequest, Shift, TimeSlot
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
import hashlib
import base64
import uuid

# Register custom filters
class BookingStatusFilter(admin.SimpleListFilter):
    title = 'Booking Status'
    parameter_name = 'booking_status'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('tomorrow', 'Tomorrow'),
            ('this_week', 'This Week'),
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
            ('completed', 'Completed'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        
        if self.value() == 'today':
            return queryset.filter(date=today)
        if self.value() == 'tomorrow':
            return queryset.filter(date=tomorrow)
        if self.value() == 'this_week':
            return queryset.filter(date__gte=today, date__lte=week_end)
        if self.value() == 'pending':
            return queryset.filter(status='pending')
        if self.value() == 'confirmed':
            return queryset.filter(status='confirmed')
        if self.value() == 'cancelled':
            return queryset.filter(status='cancelled')
        if self.value() == 'completed':
            return queryset.filter(status='completed')

class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ('name', 'price', 'duration', 'is_active')
    show_change_link = True
    verbose_name = "Service"
    verbose_name_plural = "Services"

class EmployeeInline(admin.TabularInline):
    model = Employee
    extra = 0
    fields = ('name', 'phone', 'email', 'is_active')
    show_change_link = True
    verbose_name = "Staff Member"
    verbose_name_plural = "Staff Members"

class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ('customer', 'service', 'employee', 'date', 'time', 'status')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True
    verbose_name = "Appointment"
    verbose_name_plural = "Appointments"
    ordering = ('-date', '-time')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show recent and upcoming bookings in the inline view
        today = timezone.now().date()
        return qs.filter(date__gte=today - timedelta(days=7))

class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0
    fields = ('day_of_week', 'start_time', 'end_time', 'is_active')

class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 0
    fields = ('date', 'start_time', 'end_time', 'is_available')
    readonly_fields = ('date', 'start_time', 'end_time')
    can_delete = False
    max_num = 0  # Don't allow adding time slots directly

class ShiftAdmin(admin.ModelAdmin):
    list_display = ('employee', 'get_day_display', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'day_of_week', 'business')
    search_fields = ('employee__name', 'business__name')
    
    def get_day_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_display.short_description = 'Day'
    
    def generate_time_slots_for_next_week(self, request, queryset):
        from datetime import datetime, timedelta
        
        # Get the start of next week (Monday)
        today = datetime.now().date()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # If today is Monday, get next Monday
        next_monday = today + timedelta(days=days_until_monday)
        
        slots_created = 0
        for shift in queryset:
            if not shift.is_active:
                continue
                
            if shift.shift_type == 'recurring':
                # Generate slots for the appropriate day next week
                target_date = next_monday + timedelta(days=shift.day_of_week)
                slots = shift.generate_time_slots(date=target_date)
                slots_created += len(slots)
            elif shift.shift_type == 'one_time':
                # Only generate slots if the specific date is within the next week
                if next_monday <= shift.specific_date < next_monday + timedelta(days=7):
                    slots = shift.generate_time_slots()
                    slots_created += len(slots)
        
        self.message_user(request, f"Generated {slots_created} time slots for next week.")
    
    generate_time_slots_for_next_week.short_description = "Generate time slots for next week"
    
    def generate_time_slots_for_next_month(self, request, queryset):
        from datetime import datetime, timedelta
        
        # Get the start of next month
        today = datetime.now().date()
        next_month = today.replace(day=1) + timedelta(days=32)
        next_month_start = next_month.replace(day=1)
        next_month_end = (next_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        slots_created = 0
        for shift in queryset:
            if not shift.is_active:
                continue
                
            if shift.shift_type == 'recurring':
                # Generate slots for all occurrences of this day of week in the next month
                current_date = next_month_start
                while current_date <= next_month_end:
                    if current_date.weekday() == shift.day_of_week:
                        slots = shift.generate_time_slots(date=current_date)
                        slots_created += len(slots)
                    current_date += timedelta(days=1)
            elif shift.shift_type == 'one_time':
                # Only generate slots if the specific date is within the next month
                if next_month_start <= shift.specific_date <= next_month_end:
                    slots = shift.generate_time_slots()
                    slots_created += len(slots)
        
        self.message_user(request, f"Generated {slots_created} time slots for next month.")
    
    generate_time_slots_for_next_month.short_description = "Generate time slots for next month"
    
    class Media:
        js = ('admin/js/shift_form.js',)
        css = {
            'all': ('admin/css/shift_form.css',)
        }

class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('shift', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('shift__employee__name',)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'phone', 'email', 'is_active', 'services_count', 'employees_count', 'today_bookings', 'account_setup_link')
    list_filter = ('is_active',)
    search_fields = ('name', 'owner__username', 'phone', 'email')
    inlines = [ServiceInline, EmployeeInline]
    fieldsets = (
        ('Business Information', {
            'fields': ('name', 'owner', 'description', 'is_active')
        }),
        ('Account Setup', {
            'fields': ('account_setup_link',),
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Business Hours', {
            'fields': ('opening_hours',)
        }),
        ('Images', {
            'fields': ('main_image', 'image1', 'image2', 'image3', 'image4'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'account_setup_link')
    actions = ['generate_account_setup_links']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(owner=request.user)
        return qs
    
    def services_count(self, obj):
        count = obj.services.count()
        url = reverse('admin:businesses_service_changelist') + f'?business__id__exact={obj.id}'
        return format_html('<a href="{}">{} Services</a>', url, count)
    services_count.short_description = "Services"
    
    def employees_count(self, obj):
        count = obj.employees.count()
        url = reverse('admin:businesses_employee_changelist') + f'?business__id__exact={obj.id}'
        return format_html('<a href="{}">{} Staff</a>', url, count)
    employees_count.short_description = "Staff"
    
    def today_bookings(self, obj):
        today = timezone.now().date()
        count = obj.bookings.filter(date=today).count()
        url = reverse('admin:businesses_booking_changelist') + f'?business__id__exact={obj.id}&date__exact={today}'
        color = "red" if count > 0 else "inherit"
        return format_html('<a href="{}" style="color: {};">{} Today</a>', url, color, count)
    today_bookings.short_description = "Today's Bookings"
    
    def account_setup_link(self, obj):
        """
        Generate a link for the business owner to set up their account
        """
        if not obj.pk:
            return '-'
            
        # Generate a token
        import hashlib
        import base64
        
        # Create a token with business ID and email hash
        email_hash = hashlib.md5(obj.email.encode()).hexdigest()
        token_data = f"{obj.pk}|{email_hash}"
        token = base64.b64encode(token_data.encode()).decode()
        
        # Generate the URL
        from django.urls import reverse
        url = reverse('businesses:business_account_setup', args=[token])
        
        # Return a clickable link
        return format_html(
            '<a href="{}" target="_blank" class="button">Setup Link</a>'
            '<div class="help">Share this link with the business owner</div>',
            url
        )
    account_setup_link.short_description = 'Account Setup'

    def generate_account_setup_links(self, request, queryset):
        """
        Generate account setup links for selected businesses
        """
        import hashlib
        import base64
        from django.urls import reverse
        
        links = []
        for business in queryset:
            # Create a token with business ID and email hash
            email_hash = hashlib.md5(business.email.encode()).hexdigest()
            token_data = f"{business.pk}|{email_hash}"
            token = base64.b64encode(token_data.encode()).decode()
            
            # Generate the URL
            url = request.build_absolute_uri(reverse('businesses:business_account_setup', args=[token]))
            links.append(f"{business.name}: {url}")
        
        # Display the links
        message = "<strong>Account Setup Links:</strong><br>"
        message += "<ul>"
        for link in links:
            message += f"<li>{link}</li>"
        message += "</ul>"
        message += "<p>Share these links with the respective business owners.</p>"
        
        self.message_user(request, format_html(message), level=messages.SUCCESS)
    generate_account_setup_links.short_description = "Generate account setup links for selected businesses"

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'price', 'duration', 'is_active')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'business__name')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'phone', 'email', 'is_active')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'business__name', 'phone', 'email')
    filter_horizontal = ('services',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'get_services', 'get_date', 'get_time', 'status')
    list_filter = ('status', 'business')
    search_fields = ('customer__username',)
    filter_horizontal = ('services', 'time_slots')
    
    def get_services(self, obj):
        return ", ".join([service.name for service in obj.services.all()])
    get_services.short_description = 'Services'
    
    def get_date(self, obj):
        first_slot = obj.time_slots.order_by('date', 'start_time').first()
        return first_slot.date if first_slot else obj.date
    get_date.short_description = 'Date'
    
    def get_time(self, obj):
        first_slot = obj.time_slots.order_by('date', 'start_time').first()
        return first_slot.start_time if first_slot else obj.time
    get_time.short_description = 'Time'

@admin.register(BusinessRequest)
class BusinessRequestAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'business_type', 'email', 'status', 'created_at')
    list_filter = ('status', 'business_type')
    search_fields = ('business_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')

# Register the models
admin.site.register(Shift, ShiftAdmin)
admin.site.register(TimeSlot, TimeSlotAdmin)
