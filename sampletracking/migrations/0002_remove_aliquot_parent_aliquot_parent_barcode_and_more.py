# Generated by Django 5.0.2 on 2024-03-01 20:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aliquot',
            name='parent',
        ),
        migrations.AddField(
            model_name='aliquot',
            name='parent_barcode',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='aliquots', to='sampletracking.crudesample', to_field='barcode'),
        ),
        migrations.AlterField(
            model_name='extract',
            name='parent',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='extracts', to='sampletracking.aliquot', to_field='barcode'),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='clean_library_conc',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='date_sequenced',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='diluted_qubit_conc',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='parent',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='sampletracking.extract'),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='qubit_conc',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
