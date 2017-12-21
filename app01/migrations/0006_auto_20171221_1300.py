# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-21 13:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0005_auto_20171215_0848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(max_length=32, verbose_name='角色名称:'),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='age',
            field=models.IntegerField(verbose_name='年龄:'),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='name',
            field=models.CharField(max_length=32, verbose_name='用户名称:'),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='password',
            field=models.CharField(max_length=32, verbose_name='密码:'),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='sex',
            field=models.CharField(max_length=32, verbose_name='性别:'),
        ),
    ]
