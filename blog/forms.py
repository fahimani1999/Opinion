from django import forms
from .models import BlogPost, Comment, PostRating


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title'
            }),

            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Write your blog post...'
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your comment...'
            }),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = PostRating
        fields = ['rating']

        widgets = {
            'rating': forms.Select(
                choices=[
                    (1, '1 Star'),
                    (2, '2 Stars'),
                    (3, '3 Stars'),
                    (4, '4 Stars'),
                    (5, '5 Stars'),
                ],
                attrs={
                    'class': 'form-control'
                }
            )
        }