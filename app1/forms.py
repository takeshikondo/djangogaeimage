from django import forms
from .models import Photo


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ('image',)
 
class ImageForm(forms.Form):
    image = forms.ImageField()
    
class ImageForm2(forms.Form):
    name = forms.CharField(
            label='Name',
            max_length=20,
            required=True,
            widget=forms.TextInput(),
            )
    image = forms.ImageField()       