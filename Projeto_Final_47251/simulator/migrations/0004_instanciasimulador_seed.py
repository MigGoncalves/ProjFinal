# Generated by Django 5.1.7 on 2025-06-04 16:36

import simulator.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0003_instanciasimulador_alter_simulador_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='instanciasimulador',
            name='seed',
            field=models.IntegerField(default=simulator.models.generate_seed),
        ),
    ]
