# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-02-26 10:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20180224_2346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clients', to='main.Region'),
        ),
        migrations.AlterField(
            model_name='client',
            name='salesman',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clients', to='main.SalesMan'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='main.Client'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='main.Product'),
        ),
    ]
