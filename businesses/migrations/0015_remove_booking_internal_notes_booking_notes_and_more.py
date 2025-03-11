# Generated by Django 5.1.6 on 2025-03-10 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businesses', '0014_rename_notes_booking_internal_notes_bookingnote'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='internal_notes',
        ),
        migrations.AddField(
            model_name='booking',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='BookingNote',
        ),
    ]
