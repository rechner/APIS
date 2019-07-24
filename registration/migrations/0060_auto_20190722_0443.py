# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-07-22 08:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import registration.models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0059_attendee_aslrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='discount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registration.Discount'),
        ),
        migrations.AlterField(
            model_name='order',
            name='reference',
            field=models.CharField(blank=True, default=registration.models.getReference, max_length=50),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='badge',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registration.Badge'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registration.Order'),
        ),
    ]
