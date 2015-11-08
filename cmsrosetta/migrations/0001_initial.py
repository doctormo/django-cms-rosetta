# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import cms.utils.permissions


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('when', models.DateTimeField(default=django.utils.timezone.now)),
                ('lang', models.CharField(max_length=6)),
                ('kind', models.CharField(max_length=16)),
                ('page', models.CharField(max_length=255)),
                ('edited', models.PositiveIntegerField(default=0)),
                ('added', models.PositiveIntegerField(default=0)),
                ('ousted', models.BooleanField(default=False)),
                ('user', models.ForeignKey(default=cms.utils.permissions.get_current_user, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
