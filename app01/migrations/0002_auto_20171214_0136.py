# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-14 01:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Username',
            new_name='Userinfo',
        ),
    ]
