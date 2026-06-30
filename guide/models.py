from django.db import models

# Medicine Details 

class guides(models.Model):
    mname=models.CharField(null='False',verbose_name='Medicine_Name',max_length=30)
    symptoms = models.CharField(max_length=1000, null='False')
    diseases = models.CharField(max_length=1000,null='False')
    category=models.CharField(null='False',verbose_name='Type',max_length=50)
    unit=models.CharField(max_length=10,null='False',verbose_name='Unit')
    unit_price=models.FloatField(null='False',verbose_name='Unit_price')
    package_unit=models.CharField(max_length=10,null='False',verbose_name='Package_Unit')
    package_price=models.FloatField(null='False',verbose_name='Package_price')
    drug=models.CharField(max_length=20,null='False',verbose_name='Drug_Name')
    per_unit=models.CharField(max_length=10,null='False',verbose_name='per_unit')
    indication=models.CharField(max_length=100,verbose_name='Indication')
    contraindication=models.CharField(max_length=100,verbose_name='Containdication')
    caution=models.CharField(max_length=500,null='True',verbose_name='Caution')
    side_effect=models.CharField(max_length=500,null='True',verbose_name='Side-Effect')
    
    def __str__(self):
        return self.mname

