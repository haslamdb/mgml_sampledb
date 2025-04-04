# Generated by Django 5.0.2 on 2024-03-02 11:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0002_remove_aliquot_parent_aliquot_parent_barcode_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aliquot',
            name='sample_type',
        ),
        migrations.RemoveField(
            model_name='crudesample',
            name='sample_type',
        ),
        migrations.RemoveField(
            model_name='extract',
            name='sample_type',
        ),
        migrations.RemoveField(
            model_name='sequencelibrary',
            name='sample_type',
        ),
        migrations.AlterField(
            model_name='aliquot',
            name='parent_barcode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aliquots', to='sampletracking.crudesample', to_field='barcode'),
        ),
        migrations.AlterField(
            model_name='extract',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='extracts', to='sampletracking.aliquot', to_field='barcode'),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='sampletracking.extract'),
        ),
    ]
