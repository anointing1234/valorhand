# Generated by Django 5.0.7 on 2024-10-13 03:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_transaction_transaction_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='balance',
            name='daily_profit_percentage',
        ),
        migrations.RemoveField(
            model_name='balance',
            name='is_daily_savings_activated',
        ),
        migrations.RemoveField(
            model_name='balance',
            name='monthly_profit_percentage',
        ),
        migrations.RemoveField(
            model_name='balance',
            name='yearly_profit_percentage',
        ),
    ]
