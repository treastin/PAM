# Generated by Django 4.2.6 on 2023-10-27 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_pic',
            field=models.ImageField(blank=True, null=True, upload_to='user/profile_pic'),
        ),
    ]
