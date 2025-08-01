# Generated by Django 5.1.11 on 2025-07-20 11:22

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0016_remove_crudesample_sampletrack_your_id_2965c3_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='aliquot',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='crudesample',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='extract',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='historicalaliquot',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='historicalcrudesample',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='historicalextract',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='historicalsequencelibrary',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AddField(
            model_name='sequencelibrary',
            name='tube_barcode',
            field=models.CharField(blank=True, help_text='Physical tube barcode (only for box storage)', max_length=255, null=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='aliquot',
            name='barcode',
            field=models.CharField(help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='crudesample',
            name='barcode',
            field=models.CharField(help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='extract',
            name='barcode',
            field=models.CharField(help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='historicalaliquot',
            name='barcode',
            field=models.CharField(db_index=True, help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='historicalcrudesample',
            name='barcode',
            field=models.CharField(db_index=True, help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='historicalextract',
            name='barcode',
            field=models.CharField(db_index=True, help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='historicalsequencelibrary',
            name='barcode',
            field=models.CharField(db_index=True, help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='barcode',
            field=models.CharField(help_text='Unique identifier for this sample (auto-generated for plate storage)', max_length=255, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9_-]+$', 'Barcode can only contain alphanumeric characters, underscores, and hyphens.')]),
        ),
    ]
