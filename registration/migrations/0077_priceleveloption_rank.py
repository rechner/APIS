# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-08-25 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0076_event_allowonlineminorreg'),
    ]

    operations = [
        migrations.AddField(
            model_name='priceleveloption',
            name='rank',
            field=models.IntegerField(default=0),
        ),
    ]