# Generated by Django 5.1.6 on 2025-03-05 02:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0002_remove_booking_notes_booking_customer_notes_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='booking',
            options={'ordering': ['-date', '-time'], 'verbose_name': 'Appointment', 'verbose_name_plural': 'Appointments'},
        ),
        migrations.AlterModelOptions(
            name='business',
            options={'ordering': ['name'], 'verbose_name': 'Business Profile', 'verbose_name_plural': 'Business Profile'},
        ),
        migrations.AlterModelOptions(
            name='employee',
            options={'ordering': ['name'], 'verbose_name': 'Staff Member', 'verbose_name_plural': 'Staff Members'},
        ),
        migrations.AlterModelOptions(
            name='service',
            options={'ordering': ['category', 'name'], 'verbose_name': 'Service', 'verbose_name_plural': 'Services'},
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), (4, '4 - Very Good'), (5, '5 - Excellent')])),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_public', models.BooleanField(default=True)),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='businesses.business')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='businesses.employee')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='businesses.service')),
            ],
            options={
                'verbose_name': 'Review',
                'verbose_name_plural': 'Reviews',
                'ordering': ['-created_at'],
            },
        ),
    ]
