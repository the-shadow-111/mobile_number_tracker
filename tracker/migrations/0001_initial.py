# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-07 12:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='bot_user',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facebook_id', models.CharField(max_length=1000)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('profile_pic', models.URLField()),
                ('locale', models.CharField(max_length=1000)),
                ('timezone', models.CharField(max_length=1000)),
                ('gender', models.CharField(max_length=10)),
            ],
        ),
    ]