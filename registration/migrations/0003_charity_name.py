# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2018-12-24 08:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_auto_20181224_0254'),
    ]

    operations = [
        migrations.AddField(
            model_name='charity',
            name='name',
            field=models.CharField(default='Charity', max_length=200),
            preserve_default=False,
        ),
    ]
