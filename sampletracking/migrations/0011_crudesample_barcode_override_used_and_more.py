# Generated by Django 5.1.11 on 2025-07-15 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0010_alter_aliquot_box_id_alter_aliquot_freezer_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='crudesample',
            name='barcode_override_used',
            field=models.BooleanField(default=False, help_text='Indicates if barcode validation was overridden during registration'),
        ),
        migrations.AddField(
            model_name='historicalcrudesample',
            name='barcode_override_used',
            field=models.BooleanField(default=False, help_text='Indicates if barcode validation was overridden during registration'),
        ),
    ]
