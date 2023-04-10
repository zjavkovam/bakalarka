# Generated by Django 4.1.7 on 2023-04-09 10:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_rename_compound_id_compounds_id_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Compounds',
            new_name='Compound',
        ),
        migrations.RenameModel(
            old_name='Impurities',
            new_name='Impuritie',
        ),
        migrations.RenameModel(
            old_name='Peaks',
            new_name='Peak',
        ),
        migrations.RenameModel(
            old_name='Solvents',
            new_name='Solvent',
        ),
        migrations.RenameModel(
            old_name='Users',
            new_name='User',
        ),
        migrations.RenameField(
            model_name='impuritie',
            old_name='solvent_id',
            new_name='solvent',
        ),
        migrations.RenameField(
            model_name='peak',
            old_name='peak_ppm',
            new_name='ppm',
        ),
        migrations.RenameField(
            model_name='peak',
            old_name='spektrum_id',
            new_name='spektrum',
        ),
        migrations.RenameField(
            model_name='spectrum',
            old_name='compound_id',
            new_name='compound',
        ),
        migrations.RenameField(
            model_name='spectrum',
            old_name='solvent_id',
            new_name='solvent',
        ),
        migrations.RenameField(
            model_name='spectrum',
            old_name='user_id',
            new_name='user',
        ),
    ]
