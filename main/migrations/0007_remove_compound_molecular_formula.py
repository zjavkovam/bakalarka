# Generated by Django 4.2 on 2023-05-15 14:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_remove_user_password'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compound',
            name='molecular_formula',
        ),
    ]
