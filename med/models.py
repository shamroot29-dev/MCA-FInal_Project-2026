from django.db import models
from Chemist_Master.models import ChemistRegister

# Currently we did not used it
class Medicine(models.Model):
    chemist = models.ForeignKey(ChemistRegister,on_delete=models.CASCADE,default='')
    m_name=models.CharField(max_length=50)
    batch=models.CharField(max_length=30)
    mfg=models.CharField(max_length=30)
    quantity=models.IntegerField()
    rate=models.FloatField()
    amount=models.FloatField()
    formulation_CHOICES = [
    ('Syrup', 'Syrup'),
    ('Tablet', 'Tablet'),
    ('Injection', 'Injection'),
]
    formulation=models.CharField(max_length=150,choices=formulation_CHOICES)

    def __str__(self):
        return self.m_name
