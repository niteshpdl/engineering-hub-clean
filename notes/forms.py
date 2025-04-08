from django import forms
from .models import Resource, Comment

class ResourceUploadForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'department', 'semester', 
                  'file', 'direct_link', 'thumbnail', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter resource title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the resource'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'direct_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'External resource URL'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Separate tags with commas'}),
        }
        help_texts = {
            'tags': 'Separate tags with commas (e.g. calculus, linear algebra, vectors)',
        }

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        direct_link = cleaned_data.get('direct_link')
        
        if not file and not direct_link:
            raise forms.ValidationError("You must either upload a file or provide a direct link.")
        
        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']  # Use 'text' instead of 'content'
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...'
            })
        }

