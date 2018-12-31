# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-29 19:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0039_auto_20170129_1410'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffJersey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('number', models.CharField(max_length=3)),
                ('shirtSize', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration.ShirtSizes')),
            ],
        ),
    ]
