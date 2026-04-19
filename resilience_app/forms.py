from django import forms

from .constants import (
    FACTORS,
    GENDER_CHOICES,
    SCORE_CHOICES,
    TEACHER_APP_FEEDBACK_SECTIONS,
)


class AnalysisRequestForm(forms.Form):
    teacher_id = forms.CharField(max_length=128, label="Teacher ID")
    teacher_email = forms.EmailField(label="Teacher email")
    student_id = forms.CharField(max_length=128, label="Student ID")
    student_age = forms.IntegerField(min_value=1, max_value=100, label="Student age")
    student_gender = forms.CharField(max_length=64, label="Student gender")
    teacher_id = forms.CharField(max_length=128, label="ID педагога")
    student_id = forms.CharField(max_length=128, label="ID учня")
    student_age = forms.IntegerField(min_value=1, max_value=100, label="Вік учня")
    student_gender = forms.ChoiceField(
        label="Стать",
        choices=GENDER_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        initial_teacher_id = kwargs.pop("initial_teacher_id", None)
        super().__init__(*args, **kwargs)

        if initial_teacher_id:
            self.fields["teacher_id"].initial = initial_teacher_id

        for factor_key, factor in FACTORS.items():
            for item in factor["items"]:
                field_name = f"{factor_key}_{item['id']}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=SCORE_CHOICES,
                    required=False,
                    label=item["text"],
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
        return {
            str(item["id"]): self.cleaned_data.get(f"{factor_key}_{item['id']}", "")
            for item in FACTORS[factor_key]["items"]
        }


class TeacherConsentForm(forms.Form):
    teacher_id = forms.CharField(
        label="ID педагога",
        max_length=128,
        required=True,
        help_text="Використайте той самий ID, якщо Ви вже раніше заповнювали форму.",
    )
    full_name = forms.CharField(
        label="Я, ___________________________________ (ПІБ),",
        max_length=255,
        required=True,
    )
    consent_given = forms.BooleanField(
        label="Так, погоджуюсь",
        required=True,
    )


class TeacherAppFeedbackForm(forms.Form):
    comments = forms.CharField(
        label="Загальні коментарі",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for section_key, section in TEACHER_APP_FEEDBACK_SECTIONS.items():
            for field_def in section["fields"]:
                name = field_def["name"]
                field_type = field_def["type"]
                label = field_def["label"]

                if field_type == "choice":
                    self.fields[name] = forms.ChoiceField(
                        label=label,
                        choices=field_def["choices"],
                        required=False,
                    )
                elif field_type == "multiple_choice":
                    self.fields[name] = forms.MultipleChoiceField(
                        label=label,
                        choices=field_def["choices"],
                        required=False,
                        widget=forms.CheckboxSelectMultiple,
                    )
                elif field_type == "text":
                    self.fields[name] = forms.CharField(
                        label=label,
                        required=False,
                    )
                elif field_type == "integer":
                    self.fields[name] = forms.IntegerField(
                        label=label,
                        required=False,
                        min_value=1,
                        max_value=120,
                    )
                elif field_type == "textarea":
                    self.fields[name] = forms.CharField(
                        label=label,
                        required=False,
                        widget=forms.Textarea(attrs={"rows": 4}),
                    )

    def get_feedback_responses(self):
        responses = {}
        for section_key, section in TEACHER_APP_FEEDBACK_SECTIONS.items():
            section_responses = {}
            for field_def in section["fields"]:
                name = field_def["name"]
                section_responses[name] = self.cleaned_data.get(name)
            responses[section_key] = section_responses
        return responses
