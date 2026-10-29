from django import forms

from .models import STATUSES


class UploadForm(forms.Form):
    title = forms.CharField(max_length=160, label="Review name")
    protocol = forms.FileField(label="Protocol · DOCX or text PDF")
    sap = forms.FileField(required=False, label="Statistical analysis plan · optional")
    authorised = forms.BooleanField(
        label="These are public, synthetic, or authorised redacted study documents. They contain no patient-level records or confidential partner material."
    )

    def clean(self):
        data = super().clean()
        for name in ("protocol", "sap"):
            upload = data.get(name)
            if upload and (
                upload.size > 25 * 1024 * 1024
                or not upload.name.lower().endswith((".pdf", ".docx"))
            ):
                self.add_error(name, "Use a DOCX or text PDF smaller than 25 MB.")
        return data


class DecisionForm(forms.Form):
    status = forms.ChoiceField(choices=STATUSES)
    note = forms.CharField(
        required=False, max_length=4000, widget=forms.Textarea(attrs={"rows": 3})
    )
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)


class ChatForm(forms.Form):
    message = forms.CharField(
        max_length=4000,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Ask about this finding or the supplied documents…"}
        ),
    )


class ClarificationForm(forms.Form):
    text = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Your clarification (kept separate from source evidence)",
    )
