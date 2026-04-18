from django import forms

from .constants import (
    FACTORS,
    FEEDBACK_PLACEHOLDER_QUESTIONS,
    FEEDBACK_QUESTION_CHOICES,
    GENDER_CHOICES,
    SCORE_CHOICES,
)


class AnalysisRequestForm(forms.Form):
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
        return {
            str(item["id"]): self.cleaned_data.get(f"{factor_key}_{item['id']}", "")
            for item in FACTORS[factor_key]["items"]
        }


class TeacherConsentForm(forms.Form):
    teacher_id = forms.CharField(
        label="ID педагога",
        max_length=128,
        required=True,
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
        label="Ваші коментарі",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for section_key, section in FEEDBACK_PLACEHOLDER_QUESTIONS.items():
            for item in section["items"]:
                field_name = f"{section_key}_{item['id']}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=[("", "---------")] + FEEDBACK_QUESTION_CHOICES,
                    required=False,
                    label=item["text"],
                )

    def get_feedback_responses(self):
        return {
            section_key: {
                item["id"]: self.cleaned_data.get(f"{section_key}_{item['id']}", "")
                for item in section["items"]
            }
            for section_key, section in FEEDBACK_PLACEHOLDER_QUESTIONS.items()
        }