from django import forms
from med.models import Medicine
from guide.models import guides

class MedicineForm(forms.ModelForm):
    
    class Meta:
        model = Medicine
        fields = "__all__"

class searchForm(forms.Form):
    search = forms.CharField(max_length= 200,label = "Please Do search Here")


class guideForm(forms.ModelForm):
    class Meta:
        model = guides
        fields = "__all__"