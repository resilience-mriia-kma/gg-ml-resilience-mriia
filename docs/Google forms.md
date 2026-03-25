# Google Forms Registry

Цей файл містить посилання на Google Forms, а також `entry`-ключі для автоматичного підставлення `teacher_id` через prefilled URL.

## 1. Форма поінформованої згоди та опитувальник щодо резильєнтності учнів

**Призначення:** форма для підтвердження поінформованої згоди педагога на участь у дослідженні, а також опитування щодо резильєнтності учнів.

**Base URL:**
https://docs.google.com/forms/d/e/1FAIpQLSf1S-Vb5bNXg-5EsXnHSwOIFTYvLAcPpYpfmtCgrfHbKNJdtg/viewform

**Prefilled test URL:**
https://docs.google.com/forms/d/e/1FAIpQLSf1S-Vb5bNXg-5EsXnHSwOIFTYvLAcPpYpfmtCgrfHbKNJdtg/viewform?usp=pp_url&entry.154070598=test

**`teacher_id` field key:**
`entry.154070598`

---

## 2. Форма зворотного зв’язку

**Призначення:** фінальна форма зворотного зв’язку після заповнення 10 відповідей.

**Base URL:**
https://docs.google.com/forms/d/e/1FAIpQLSdSGvCuqeWitxGla5I1-fk12XWEC-8pPomE6PKdN0DHgl6z-g/viewform

**Prefilled test URL:**
https://docs.google.com/forms/d/e/1FAIpQLSdSGvCuqeWitxGla5I1-fk12XWEC-8pPomE6PKdN0DHgl6z-g/viewform?usp=pp_url&entry.783189352=test

**`teacher_id` field key:**
`entry.783189352`

---

## Загальна логіка використання

Для кожного педагога генерується персональний `teacher_id`, який автоматично підставляється в кожну форму через prefilled URL.

Формат посилання:

```text
<BASE_URL>?usp=pp_url&<ENTRY_KEY>=<teacher_id>