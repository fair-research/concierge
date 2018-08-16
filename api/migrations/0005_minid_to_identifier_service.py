# Generated by Django 2.0.7 on 2018-07-24 18:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('admin', '0002_logentry_remove_auto_add'),
        ('api', '0004_auto_20180628_1441'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenStore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_store', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='globususer',
            name='user_ptr',
        ),
        migrations.DeleteModel(
            name='GlobusUser',
        ),
        migrations.RemoveField(
            model_name='stagebag',
            name='transfer_token',
        ),
        migrations.AddField(
            model_name='stagebag',
            name='task_catalog',
            field=models.TextField(default={}),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stagebag',
            name='files_transferred',
            field=models.IntegerField(default=0, blank=True, null=True),
            preserve_default=False,
        ),
    ]