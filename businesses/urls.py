from django.urls import path
from . import views

app_name = 'businesses'

urlpatterns = [
    path('request/', views.BusinessRequestView.as_view(), name='business_request'),
    path('request/success/', views.business_request_success, name='business_request_success'),
    path('account/setup/<str:token>/', views.business_account_setup, name='business_account_setup'),
    path('account/setup/success/', views.account_setup_success, name='account_setup_success'),
    path('employees/', views.get_employees, name='get_employees'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/<int:employee_id>/', views.get_employee_details, name='get_employee_details'),
    path('employees/<int:employee_id>/bookings/', views.get_employee_bookings, name='get_employee_bookings'),
    path('employees/<int:employee_id>/shifts/', views.get_employee_shifts, name='get_employee_shifts'),
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),
    path('services/add/', views.add_service, name='add_service'),
    path('shifts/', views.manage_shifts, name='manage_shifts'),
    path('shifts/add/', views.add_shift, name='add_shift'),
    path('shifts/<int:shift_id>/', views.update_shift, name='update_shift'),
    path('shifts/<int:shift_id>/delete/', views.delete_shift, name='delete_shift'),
    path('shifts/weekly/', views.get_weekly_shifts, name='get_weekly_shifts'),
    path('bookings/', views.get_business_bookings, name='get_business_bookings'),
    path('bookings/available-slots/', views.get_available_slots, name='get_available_slots'),
    path('bookings/create/', views.create_booking, name='create_booking'),
] 