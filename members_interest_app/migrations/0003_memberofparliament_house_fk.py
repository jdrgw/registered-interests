# Generated by Django 4.1 on 2024-09-28 15:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members_interest_app', '0002_house'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberofparliament',
            name='house_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='members_interest_app.house'),
        ),
    ]