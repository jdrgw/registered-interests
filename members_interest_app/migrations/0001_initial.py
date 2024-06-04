# Generated by Django 4.1 on 2024-06-01 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MemberOfParliament',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('api_id', models.CharField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=350)),
                ('gender', models.CharField(max_length=255, null=True)),
                ('thumbnail_url', models.URLField(blank=True, max_length=300)),
                ('constituency', models.CharField(max_length=255, null=True)),
                ('membership_start', models.DateTimeField(null=True)),
                ('membership_end', models.DateTimeField(null=True)),
                ('membership_end_reason', models.CharField(max_length=255, null=True)),
                ('membership_end_notes', models.TextField(null=True)),
                ('house', models.CharField(default='TBC', max_length=255)),
            ],
        ),
    ]