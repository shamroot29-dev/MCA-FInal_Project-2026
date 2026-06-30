from django import forms
from User_Master.models import UserRegister,UserQuery

class UserRegisterForm(forms.ModelForm):
    class Meta:
        model=UserRegister
        exclude = ('forgot_pass', 'userarea')
        error_messages = {
            'uid': {
                'required': 'Please enter the supplier email address.',
                'invalid': 'Please enter a valid email address.',
                'unique': 'A supplier account with this email already exists.',
            },
            'userpwd': {
                'required': 'Please enter a password.',
            },
            'userfname': {
                'required': 'Please enter the first name.',
            },
            'userlname': {
                'required': 'Please enter the last name.',
            },
            'useraddress': {
                'required': 'Please enter the address.',
            },
            'usercity': {
                'required': 'Please enter the city.',
            },
            'userpincode': {
                'required': 'Please enter the pincode.',
                'invalid': 'Please enter a valid pincode.',
            },
            'usercontactno': {
                'required': 'Please enter the contact number.',
                'invalid': 'Please enter a valid contact number.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usermname'].required = False

    def clean_userpwd(self):
        password = self.cleaned_data.get('userpwd', '')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password

    def clean_userpincode(self):
        pincode = self.cleaned_data.get('userpincode')
        if pincode is not None and len(str(pincode)) != 6:
            raise forms.ValidationError('Pincode must be 6 digits.')
        return pincode

    def clean_usercontactno(self):
        contact_number = self.cleaned_data.get('usercontactno')
        if contact_number is not None and len(str(contact_number)) != 10:
            raise forms.ValidationError('Contact number must be 10 digits.')
        return contact_number

class UserQueryForm(forms.ModelForm):
    class Meta:
        model=UserQuery
        fields='__all__'
    
