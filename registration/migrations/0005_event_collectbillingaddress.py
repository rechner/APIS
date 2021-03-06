# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2018-12-25 09:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_auto_20181224_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='collectBillingAddress',
            field=models.BooleanField(default=True, help_text="Disable to skip collecting a billing address for each order. Note that a billing address and buyer email is required to qualify for Square's Chargeback protection.", verbose_name='Collect Billing Address'),
        ),
    ]
