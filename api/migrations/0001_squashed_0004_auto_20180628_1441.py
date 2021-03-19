# Generated by Django 3.1.2 on 2020-10-22 17:01

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('api', '0001_initial'), ('api', '0002_stagebag'), ('api', '0003_add_user_to_models_20180105_2329'), ('api', '0004_auto_20180628_1441')]

    initial = True

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobusUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, to=settings.AUTH_USER_MODEL)),
                ('uuid', models.UUIDField(editable=False, primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Bag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minid_id', models.CharField(max_length=30)),
                ('minid_email', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StageBag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_endpoint', models.CharField(max_length=512)),
                ('destination_path_prefix', models.CharField(max_length=255)),
                ('bag_minids', models.TextField()),
                ('transfer_token', models.CharField(max_length=255)),
                ('transfer_catalog', models.TextField()),
                ('error_catalog', models.TextField()),
                ('transfer_task_ids', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]