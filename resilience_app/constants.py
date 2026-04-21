from collections import OrderedDict

RESILIENCE_LEVEL_UKRAINIAN = {
    "low": "низький",
    "medium": "середній",
    "high": "високий",
}

SCORE_CHOICES = [
    ("", "---------"),
    ("0", "0 - низький рівень"),
    ("1", "1 - середній рівень"),
    ("2", "2 - високий рівень"),
    ("NA", "NA - недостатньо інформації"),
]

GENDER_CHOICES = [
    ("male", "чоловіча"),
    ("female", "жіноча"),
]

YES_PARTIAL_NO_CHOICES = [
    ("yes", "Так"),
    ("partial", "Частково"),
    ("no", "Ні"),
]

EXPERIENCE_CHOICES = [
    ("up_to_3", "До 3 років"),
    ("3_10", "3–10 років"),
    ("10_20", "10–20 років"),
    ("over_20", "Більше 20 років"),
]

SCHOOL_LEVEL_CHOICES = [
    ("primary", "Початкова школа"),
    ("middle", "Середня школа"),
    ("high", "Старша школа"),
]

RANGE_STUDENTS_CHOICES = [
    ("1_3", "1–3"),
    ("4_7", "4–7"),
    ("8_12", "8–12"),
    ("over_12", "Більше 12"),
]

LIKERT_5_CHOICES = [
    ("", "---------"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
]

ID_FIELDS = ["student_id", "student_age", "student_gender"]

FEEDBACK_TRIGGER_COUNT = 10

FACTORS = OrderedDict(
    {
        "family_support": {
            "label": "Підтримка сім'ї",
            "items": [
                {
                    "id": 3,
                    "text": "Батьки проявляють інтерес до досвіду дитини (цікавляться її справами, переживаннями)",
                },
                {
                    "id": 5,
                    "text": "Батьки реагують на труднощі дитини підтримуюче (обговорюють, допомагають, пояснюють)",
                },
                {
                    "id": 11,
                    "text": "Після взаємодії з батьками емоційний стан дитини зазвичай стабілізується або покращується",
                },
                {
                    "id": 15,
                    "text": "Батьки демонструють прийняття дитини (критикують дії, а не особистість)",
                },
                {
                    "id": 18,
                    "text": "У взаємодії батьків з дитиною не спостерігаються приниження, залякування або різкий осуд",
                },
                {
                    "id": 23,
                    "text": "У взаємодії з батьками дитина має можливість висловлюватися без знецінення",
                },
            ],
        },
        "optimism": {
            "label": "Оптимізм",
            "items": [
                {
                    "id": 1,
                    "text": "У складних ситуаціях може знаходити позитивні аспекти",
                },
                {
                    "id": 6,
                    "text": "У поведінці переважає спокійний або позитивний емоційний фон",
                },
                {
                    "id": 12,
                    "text": "Виглядає задоволеною у повсякденній діяльності або взаємодії",
                },
                {
                    "id": 19,
                    "text": "Проявляє позитивні емоції у взаємодії (посмішка, зацікавленість, включеність)",
                },
                {
                    "id": 24,
                    "text": "Виглядає щасливою",
                },
                {
                    "id": 26,
                    "text": "У складних ситуаціях, підбадьорює однолітків",
                },
            ],
        },
        "goal_directedness": {
            "label": "Цілеспрямованість / копінг",
            "items": [
                {
                    "id": 2,
                    "text": "У складних ситуаціях використовує знайомі способи подолання труднощів",
                },
                {
                    "id": 8,
                    "text": "Ставить перед собою цілі і намагається їх досягати",
                },
                {
                    "id": 13,
                    "text": "Якщо завдання складне, пробує різні способи його виконання",
                },
                {
                    "id": 20,
                    "text": "Ініціює та підтримує взаємодію з іншими",
                },
                {
                    "id": 25,
                    "text": "Може висловити незгоду у прийнятний спосіб (без агресії)",
                },
                {
                    "id": 27,
                    "text": "У складних ситуаціях намагається знайти рішення, а не відмовляється від діяльності",
                },
            ],
        },
        "social_connections": {
            "label": "Соціальні зв’язки",
            "items": [
                {
                    "id": 7,
                    "text": "Вступає у контакт з новими людьми без виражених труднощів",
                },
                {
                    "id": 9,
                    "text": "Підтримує стабільні стосунки або дружні зв’язки",
                },
                {
                    "id": 14,
                    "text": "У взаємодії поводиться впевнено (без надмірної тривоги або уникання)",
                },
                {
                    "id": 16,
                    "text": "Легко взаємодіє з однолітками у різних ситуаціях",
                },
                {
                    "id": 21,
                    "text": "Знаходить спільну мову з різними людьми",
                },
            ],
        },
        "health": {
            "label": "Здоров'я",
            "items": [
                {
                    "id": 4,
                    "text": "Протягом дня проявляє достатній рівень енергії та залученості в діяльність",
                },
                {
                    "id": 10,
                    "text": "Виглядає фізично бадьорою",
                },
                {
                    "id": 17,
                    "text": "У вільний час обирає рухливі ігри або заняття (біганина, спортивні ігри, активності на свіжому повітрі)",
                },
                {
                    "id": 22,
                    "text": "Турбується про своє здоров’я (гігієна, харчування, сон, шкідливі звички)",
                },
            ],
        },
    }
)

TEACHER_APP_FEEDBACK_SECTIONS = OrderedDict(
    {
        "general_information": {
            "label": "Блок 1. Загальна інформація",
            "fields": [
                {
                    "name": "teaching_experience",
                    "type": "choice",
                    "label": "Ваш стаж педагогічної діяльності",
                    "choices": EXPERIENCE_CHOICES,
                    "help_text": "Оберіть діапазон, який найкраще відповідає Вашому педагогічному стажу.",
                },
                {
                    "name": "school_levels",
                    "type": "multiple_choice",
                    "label": "Клас(и), з якими Ви працюєте",
                    "choices": SCHOOL_LEVEL_CHOICES,
                    "help_text": "Можна обрати кілька варіантів.",
                },
                {
                    "name": "subject",
                    "type": "text",
                    "label": "Предмет",
                },
                {
                    "name": "teacher_gender",
                    "type": "choice",
                    "label": "Стать",
                    "choices": GENDER_CHOICES,
                },
                {
                    "name": "teacher_age",
                    "type": "integer",
                    "label": "Вік",
                    "help_text": "Вкажіть повний вік у роках.",
                },
            ],
        },
        "tool_experience": {
            "label": "Блок 2. Досвід використання інструменту",
            "fields": [
                {
                    "name": "completed_student_assessment",
                    "type": "choice",
                    "label": "Чи змогли Ви завершити оцінювання учнів за допомогою інструменту?",
                    "choices": YES_PARTIAL_NO_CHOICES,
                    "help_text": "Оберіть один варіант: Так / Частково / Ні.",
                },
                {
                    "name": "students_evaluated_range",
                    "type": "choice",
                    "label": "Скільки учнів Ви оцінили?",
                    "choices": RANGE_STUDENTS_CHOICES,
                    "help_text": "Оберіть приблизний діапазон кількості оцінених учнів.",
                },
                {
                    "name": "ease_of_use",
                    "type": "choice",
                    "label": "Наскільки легко було використовувати інструмент?",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - дуже складно, 5 - дуже легко.",
                },
                {
                    "name": "tool_experience_comments",
                    "type": "textarea",
                    "label": "Ваші коментарі щодо досвіду користування",
                },
            ],
        },
        "acceptability": {
            "label": "Блок 3. Прийнятність (Acceptability)",
            "fields": [
                {
                    "name": "tool_is_useful",
                    "type": "choice",
                    "label": "Інструмент є корисним у моїй роботі",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не погоджуюсь, 5 - повністю погоджуюсь.",
                },
                {
                    "name": "comfortable_to_use",
                    "type": "choice",
                    "label": "Мені було комфортно використовувати цей інструмент",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не погоджуюсь, 5 - повністю погоджуюсь.",
                },
                {
                    "name": "would_recommend_tool",
                    "type": "choice",
                    "label": "Я б рекомендував(ла) цей інструмент іншим вчителям",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - точно ні, 5 - точно так.",
                },
                {
                    "name": "acceptability_comments",
                    "type": "textarea",
                    "label": "Ваші коментарі",
                },
            ],
        },
        "appropriateness": {
            "label": "Блок 4. Відповідність (Appropriateness)",
            "fields": [
                {
                    "name": "fits_student_needs",
                    "type": "choice",
                    "label": "Інструмент відповідає потребам моїх учнів",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не відповідає, 5 - повністю відповідає.",
                },
                {
                    "name": "fits_school_context",
                    "type": "choice",
                    "label": "Інструмент відповідає умовам моєї школи",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не відповідає, 5 - повністю відповідає.",
                },
                {
                    "name": "questions_reflect_real_classroom",
                    "type": "choice",
                    "label": "Питання інструменту відображають реальні ситуації в класі",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не відображають, 5 - повністю відображають.",
                },
                {
                    "name": "appropriateness_comments",
                    "type": "textarea",
                    "label": "Ваші коментарі",
                },
            ],
        },
        "feasibility": {
            "label": "Блок 5. Здійсненність (Feasibility)",
            "fields": [
                {
                    "name": "can_use_daily",
                    "type": "choice",
                    "label": "Я можу використовувати цей інструмент у своїй щоденній роботі",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не можу, 5 - повністю можу.",
                },
                {
                    "name": "not_too_time_consuming",
                    "type": "choice",
                    "label": "Заповнення інструменту не займає надто багато часу",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не погоджуюсь, 5 - повністю погоджуюсь.",
                },
                {
                    "name": "understand_integration",
                    "type": "choice",
                    "label": "Я розумію, як інтегрувати цей інструмент у свою практику",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не розумію, 5 - повністю розумію.",
                },
                {
                    "name": "feasibility_comments",
                    "type": "textarea",
                    "label": "Ваші коментарі",
                },
            ],
        },
        "usability": {
            "label": "Блок 6. Зручність використання (Usability)",
            "fields": [
                {
                    "name": "interface_clear",
                    "type": "choice",
                    "label": "Інтерфейс системи є зрозумілим",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не зрозумілий, 5 - повністю зрозумілий.",
                },
                {
                    "name": "instructions_clear",
                    "type": "choice",
                    "label": "Інструкції були зрозумілими",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не зрозумілі, 5 - повністю зрозумілі.",
                },
                {
                    "name": "easy_to_navigate",
                    "type": "choice",
                    "label": "Я легко орієнтувався(лась) у системі",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - було дуже важко орієнтуватися, 5 - дуже легко.",
                },
                {
                    "name": "usability_comments",
                    "type": "textarea",
                    "label": "Ваші коментарі",
                },
            ],
        },
        "llm_evaluation": {
            "label": "Блок 7. Оцінка ШІ-агента (LLM)",
            "fields": [
                {
                    "name": "recommendations_clear",
                    "type": "choice",
                    "label": "Рекомендації системи були зрозумілими",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не зрозумілі, 5 - повністю зрозумілі.",
                },
                {
                    "name": "recommendations_relevant",
                    "type": "choice",
                    "label": "Рекомендації виглядали релевантними до ситуацій учнів",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не релевантні, 5 - повністю релевантні.",
                },
                {
                    "name": "recommendations_practical",
                    "type": "choice",
                    "label": "Рекомендації були практичними для використання",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не практичні, 5 - дуже практичні.",
                },
                {
                    "name": "trust_recommendations",
                    "type": "choice",
                    "label": "Я довіряю рекомендаціям системи",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не довіряю, 5 - повністю довіряю.",
                },
            ],
        },
        "safety_ethics": {
            "label": "Блок 8. Безпека та етика",
            "fields": [
                {
                    "name": "no_stigmatization_risk",
                    "type": "choice",
                    "label": "Система не створює ризику стигматизації учнів",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не погоджуюсь, 5 - повністю погоджуюсь.",
                },
                {
                    "name": "understand_limitations",
                    "type": "choice",
                    "label": "Я розумію обмеження системи",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не розумію, 5 - повністю розумію.",
                },
                {
                    "name": "not_a_diagnosis",
                    "type": "choice",
                    "label": "Я не сприймаю рекомендації як “діагноз”",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - зовсім не погоджуюсь, 5 - повністю погоджуюсь.",
                },
            ],
        },
        "intention_to_use": {
            "label": "Блок 9. Намір використання",
            "fields": [
                {
                    "name": "would_use_future",
                    "type": "choice",
                    "label": "Я б використовував(ла) цей інструмент у майбутньому",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - точно ні, 5 - точно так.",
                },
                {
                    "name": "would_use_regularly",
                    "type": "choice",
                    "label": "Я б використовував(ла) цей інструмент регулярно",
                    "choices": LIKERT_5_CHOICES,
                    "help_text": "1 - точно ні, 5 - точно так.",
                },
            ],
        },
        "open_questions": {
            "label": "Блок 10. Відкриті питання",
            "fields": [
                {
                    "name": "most_useful_part",
                    "type": "textarea",
                    "label": "Що було найбільш корисним у цьому інструменті?",
                },
                {
                    "name": "unclear_or_difficult",
                    "type": "textarea",
                    "label": "Що було незрозумілим або складним?",
                },
                {
                    "name": "doubt_or_discomfort",
                    "type": "textarea",
                    "label": "Чи були рекомендації, які викликали сумніви або дискомфорт?",
                },
                {
                    "name": "suggested_changes",
                    "type": "textarea",
                    "label": "Які зміни Ви б запропонували?",
                },
            ],
        },
        "student_work_experience": {
            "label": "Блок 11. Досвід роботи з учнями",
            "fields": [
                {
                    "name": "helped_understand_students",
                    "type": "choice",
                    "label": "Чи допоміг інструмент Вам краще зрозуміти учнів?",
                    "choices": YES_PARTIAL_NO_CHOICES,
                    "help_text": "Оберіть один варіант: Так / Частково / Ні.",
                },
                {
                    "name": "changed_work_after_tool",
                    "type": "textarea",
                    "label": "Чи змінили Ви щось у своїй роботі після використання інструменту?",
                },
            ],
        },
    }
)
