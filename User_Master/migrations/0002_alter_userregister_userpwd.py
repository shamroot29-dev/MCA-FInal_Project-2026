from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_Master', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userregister',
            name='userpwd',
            field=models.CharField(max_length=128, verbose_name='Password'),
        ),
    ]
