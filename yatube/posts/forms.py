from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) >= 2000:
            raise forms.ValidationError('Слишком длинный текст!')
        for word in data.split():
            if len(word) >= 60:
                raise forms.ValidationError(f'Слово "{word}" слишком длинное!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
