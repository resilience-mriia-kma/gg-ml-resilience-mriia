from django import forms

from .constants import FACTORS, SCORE_CHOICES


class AnalysisRequestForm(forms.Form):
    teacher_id = forms.CharField(max_length=128, label="Teacher ID")
    teacher_email = forms.EmailField(label="Teacher email")
    student_id = forms.CharField(max_length=128, label="Student ID")
    student_age = forms.IntegerField(min_value=1, max_value=100, label="Student age")
    student_gender = forms.CharField(max_length=64, label="Student gender")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for factor_key, factor in FACTORS.items():
            for item in factor["items"]:
                field_name = f"{factor_key}_{item}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=SCORE_CHOICES,
                    required=False,
                    label=f"Item {item}",
                )

    def get_scores(self, factor_key):
        return [
            self.cleaned_data.get(f"{factor_key}_{item}", "")
            for item in FACTORS[factor_key]["items"]
        ]


class TeacherFeedbackForm(forms.Form):
    teacher_id = forms.CharField(widget=forms.HiddenInput())
    teacher_email = forms.EmailField(widget=forms.HiddenInput())
    forms_completed = forms.IntegerField(widget=forms.HiddenInput())

    rating = forms.ChoiceField(
        label="How useful was the system?",
        choices=[
            ("1", "1 - not useful"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5 - very useful"),
        ],
        widget=forms.RadioSelect,
    )
    comments = forms.CharField(
        label="Comments",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )