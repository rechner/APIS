# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-12-23 22:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0030_auto_20161221_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='registrationToken',
            field=models.CharField(default=12345, max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='discount',
            name='oneTime',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='discount',
            name='reason',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
