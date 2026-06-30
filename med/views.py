from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from med.forms import MedicineForm
from med.models import Medicine
from .forms import searchForm,guideForm

from django import views
from Chemist_Master.models import ChemistRegister
# Create your views here.

# Using only on function def medi from this view.py

#used For adding new medicines 
def medi(request):
    form=guideForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect('chemist:Uploaded_Medi')
    else:
        form = guideForm()
    return render(request,'medindex.html',{'form':form})

def show1(request):
    abc=Medicine.objects.all()
    return render(request,"show.html",{'a': abc})

def show(request,para):  
    
    medi = Medicine.objects.all() if para == None else Medicine.objects.filter(m_name__icontains = para) 
    form = searchForm(data = request.POST) 

    return render(request,"search.html",{'medi':medi,'form': form})  
  

def update(request, id):  
    medi = Medicine.objects.get(id=id)  
    form = MedicineForm(request.POST or None, instance = medi)  
    if form.is_valid():  
        form.save()  
        return redirect("/med/show")  
    return render(request,'edit.html', {'medi': form})  

def destroy(request, id):  
    medi = Medicine.objects.get(id=id)  
    medi.delete()  
    return redirect("/med/show")  

def mediProfileList(request,  para = None):
    abc=Medicine.objects.all() if para == None else Medicine.objects.filter(name__icontains = para)
    return render(request,'viewprofile.html',{'profiles' : abc})

class Search(views.View):

    def get(self, request, *args, **kwargs):
        form = searchForm(initial={'search' : ''})
        
        return render(request,'search.html',{'form': form})

    def post(self, request, *args, **kwargs):
        form = searchForm(data = request.POST)
        if form.is_valid():
            return redirect('med:profilesearch',para = form.cleaned_data['search'])   
        else:
            return render(request,'search.html',{'form': form})
