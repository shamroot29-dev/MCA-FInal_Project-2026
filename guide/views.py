from pathlib import Path

from django.conf import settings
from django.shortcuts import render,get_object_or_404
from django.db.models import Q
from .models import guides
from django.core.paginator import Paginator
import csv


def CSV(request):
    csv_path = Path(settings.BASE_DIR) / 'guide' / 'static' / 'Data.csv'

    with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row.get('mname'):
                continue
            guides.objects.update_or_create(
                mname=row['mname'],
                defaults={
                    'symptoms': row.get('symptoms', ''),
                    'diseases': row.get('diseases', ''),
                    'category': row.get('category', ''),
                    'unit': row.get('unit', ''),
                    'unit_price': row.get('unit_price') or 0,
                    'package_unit': row.get('package_unit', ''),
                    'package_price': row.get('package_price') or 0,
                    'drug': row.get('drug', ''),
                    'per_unit': row.get('per_unit', ''),
                    'indication': row.get('indication', ''),
                    'contraindication': row.get('contraindication', ''),
                    'caution': row.get('caution', ''),
                    'side_effect': row.get('side_effect', ''),
                }
            )

    query = request.GET.get('q', '').strip()
    medicine = request.GET.get('medicine', '').strip()
    symptom = request.GET.get('symptom', '').strip()
    disease = request.GET.get('disease', '').strip()

    guide = guides.objects.all().order_by('mname')
    if query:
        guide = guide.filter(
            Q(mname__icontains=query) |
            Q(drug__icontains=query) |
            Q(symptoms__icontains=query) |
            Q(diseases__icontains=query)
        )
    if medicine:
        guide = guide.filter(Q(mname__icontains=medicine) | Q(drug__icontains=medicine))
    if symptom:
        guide = guide.filter(symptoms__icontains=symptom)
    if disease:
        guide = guide.filter(diseases__icontains=disease)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    paginator = Paginator(guide, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'Medicine.html', {
        'key': guide,
        'page_obj': page_obj,
        'query': query,
        'medicine': medicine,
        'symptom': symptom,
        'disease': disease,
        'query_string': query_params.urlencode(),
        'result_count': guide.count(),
    })

def View(request, pk):
    guide= get_object_or_404(guides,id=pk)    
    return render(request,'view.html',{'key':guide})
