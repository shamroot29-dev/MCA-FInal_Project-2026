from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chemist_Master', '0005_supplier_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='sk_bills',
            name='payment_status',
            field=models.CharField(default='Paid', max_length=20),
        ),
    ]
