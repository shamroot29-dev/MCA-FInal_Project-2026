from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chemist_Master', '0002_auto_20220516_1142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chemistregister',
            name='chemistpwd',
            field=models.CharField(max_length=128, verbose_name='Password'),
        ),
    ]
