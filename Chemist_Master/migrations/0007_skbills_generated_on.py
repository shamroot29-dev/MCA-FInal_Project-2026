from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chemist_Master', '0006_skbills_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='sk_bills',
            name='generated_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
