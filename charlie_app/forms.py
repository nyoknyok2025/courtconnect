from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CaptchaAuthenticationForm(AuthenticationForm):
    captcha_confirmed = forms.BooleanField(
        required=True,
        label="I'm not a robot",
        initial=False,
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields['captcha_confirmed'].required = True
        self.fields['captcha_confirmed'].widget.attrs.update({'class': 'captcha-checkbox'})

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('captcha_confirmed'):
            raise forms.ValidationError("Please confirm you are not a robot.")
        return cleaned_data
