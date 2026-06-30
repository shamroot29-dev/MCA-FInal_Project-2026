from django import template

from Chemist_Master.models import StockDetails, ProductDetails

register = template.Library()

@register.filter(name='qty_check')
def qty_check(product):
    try:
        pro = StockDetails.objects.get(supplier=product.supplier, productName=product.productname)
        return int(product.productquantity) <= int(pro.quantity)
    except StockDetails.DoesNotExist:
        return False

@register.filter(name='qty_data')
def qty_data(product):
    try:
        pro = StockDetails.objects.get(supplier=product.supplier, productName=product.productname)
        return int(pro.quantity)
    except StockDetails.DoesNotExist:
        return 0
