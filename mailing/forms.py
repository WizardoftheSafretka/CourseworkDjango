from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Recipient, Message, Mailing


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ != 'CheckboxSelectMultiple':
                if hasattr(field.widget, 'attrs'):
                    field.widget.attrs['class'] = 'form-control'


class RecipientForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Recipient
        fields = '__all__'


class MessageForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = '__all__'


class MailingForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['name', 'start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Select(attrs={'class': 'form-control'}),
            'recipients': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'recipients' in self.fields:
            self.fields['recipients'].queryset = Recipient.objects.all()
            self.fields['recipients'].required = True
            self.fields['recipients'].label = "Получатели"

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        recipients = cleaned_data.get('recipients')

        if not recipients:
            raise ValidationError({
                'recipients': 'Выберите хотя бы одного получателя'
            })

        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError({
                    'end_time': 'Дата окончания должна быть позже даты начала'
                })

        if start_time and start_time < timezone.now():
            raise ValidationError({
                'start_time': 'Дата начала не может быть в прошлом'
            })

        return cleaned_data