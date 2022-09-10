# Импортируем модуль forms, из него возьмём класс ModelForm
from django import forms

# Импортируем модель, чтобы связать с ней форму
from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        label = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Содержимое поста должно быть не пустым',
            'group': 'Выберите группу. Не обязательно',
            'image': 'Поле для картинки (необязательное)'
        }

    def clean_text(self):
        data = self.cleaned_data['text']

        # Если нет текста - считаем это ошибкой
        if not data.lower():
            raise forms.ValidationError('Вы обязательно должны заполнить пост')

        # Метод-валидатор обязательно должен вернуть очищенные данные,
        # даже если не изменил их
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        label = {
            'text': 'Текст поста'
        }
        help_texts = {
            'text': 'Содержимое комментария должно быть не пустым'
        }

    def clean_text(self):
        data = self.cleaned_data['text']

        # Если нет текста - считаем это ошибкой
        if not data.lower():
            raise forms.ValidationError(
                'Вы обязательно должны заполнить комментарий'
            )

        # Метод-валидатор обязательно должен вернуть очищенные данные,
        # даже если не изменил их
        return data
