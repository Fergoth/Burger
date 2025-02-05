from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        primary_key=True
    )
    updated_at = models.DateTimeField(
        'время jобращения к API',
        default=timezone.now,
        db_index=True
    )
    latitude = models.DecimalField(
        'Широта',
        max_digits=9,
        decimal_places=6,
        null=True,
    )
    longitude = models.DecimalField(
        'Долгота',
        max_digits=9,
        decimal_places=6,
        null=True
    )
    correct_address = models.BooleanField(
        'корректность адреса',
        default=True
    )
