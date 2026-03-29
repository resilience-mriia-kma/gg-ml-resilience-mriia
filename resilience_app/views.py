from django.http import JsonResponse
from django.shortcuts import render

from .constants import FACTORS
from .forms import AnalysisRequestForm
from .models import AnalysisRequest

ID_FIELDS = ['teacher_id', 'student_id', 'student_age', 'student_gender']


def index(request):
    return JsonResponse({"status": "ok", "message": "ml-resilience-mriia"})


# TODO: these are initial demo views
# TODO: they do not reflect the final product and will be rewritten

def _group_factor_fields(form):
    groups = []
    for factor_key, factor in FACTORS.items():
        fields = [form[f'{factor_key}_{item}'] for item in factor['items']]
        groups.append({
            'label': factor['label'],
            'items': factor['items'],
            'fields': fields,
        })
    return groups



def analysis_form(request):
    success = False
    if request.method == 'POST':
        form = AnalysisRequestForm(request.POST)
        if form.is_valid():
            scores = {key: form.get_scores(key) for key in FACTORS}
            AnalysisRequest.objects.create(
                teacher_id=form.cleaned_data['teacher_id'],
                student_id=form.cleaned_data['student_id'],
                student_age=form.cleaned_data['student_age'],
                student_gender=form.cleaned_data['student_gender'],
                scores=scores,
            )
            form = AnalysisRequestForm()
            success = True
    else:
        form = AnalysisRequestForm()

    return render(request, 'resilience_app/analysis_form.html', {
        'form': form,
        'id_fields': [form[name] for name in ID_FIELDS],
        'factor_groups': _group_factor_fields(form),
        'success': success,
    })
