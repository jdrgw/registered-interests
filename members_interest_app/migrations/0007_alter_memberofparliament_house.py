# Generated by Django 4.1 on 2024-10-01 17:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members_interest_app', '0006_rename_house_fk_memberofparliament_house'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memberofparliament',
            name='house',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='members_interest_app.house'),
        ),
    ]
