# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-05-24 18:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pttrack', '0009_set_orderings_20190902_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionitem',
            name='due_date',
            field=models.DateField(help_text=b'MM/DD/YYYY'),
        ),
        migrations.AlterField(
            model_name='historicalactionitem',
            name='due_date',
            field=models.DateField(help_text=b'MM/DD/YYYY'),
        ),
    ]
