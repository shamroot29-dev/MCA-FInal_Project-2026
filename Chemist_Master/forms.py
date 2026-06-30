from django import forms
from Chemist_Master.models import ChemistRegister
from  guide.models import guides

class ChemistRegisterform(forms.ModelForm):
    class Meta:
        model=ChemistRegister
        exclude = ('forgot_pass', 'chemistarea')
        error_messages = {
            'cid': {
                'required': 'Please enter the chemist email address.',
                'invalid': 'Please enter a valid email address.',
            },
            'chemistpwd': {
                'required': 'Please enter a password.',
            },
            'chemistfname': {
                'required': 'Please enter the first name.',
            },
            'chemistlname': {
                'required': 'Please enter the last name.',
            },
            'chemistaddress': {
                'required': 'Please enter the store address.',
            },
            'chemistcity': {
                'required': 'Please enter the city.',
            },
            'chemistpincode': {
                'required': 'Please enter the pincode.',
                'invalid': 'Please enter a valid pincode.',
            },
            'chemistcontactno': {
                'required': 'Please enter the contact number.',
                'invalid': 'Please enter a valid contact number.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chemistmname'].required = False
        self.fields['chemistphoto'].required = False

    def clean_chemistpwd(self):
        password = self.cleaned_data.get('chemistpwd', '')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password

    def clean_chemistpincode(self):
        pincode = self.cleaned_data.get('chemistpincode')
        if pincode is not None and len(str(pincode)) != 6:
            raise forms.ValidationError('Pincode must be 6 digits.')
        return pincode

    def clean_chemistcontactno(self):
        contact_number = self.cleaned_data.get('chemistcontactno')
        if contact_number is not None and len(str(contact_number)) != 10:
            raise forms.ValidationError('Contact number must be 10 digits.')
        return contact_number

class guideForm(forms.ModelForm):
    class Meta:
        model = guides
        fields = "__all__"
