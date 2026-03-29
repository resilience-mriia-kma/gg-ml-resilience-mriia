# Project Requirements & Task Plan
### Resilience Screener — LLM-Assisted Recommendation System for Teachers

---

## Project Requirements

### 1. Teacher Form

- Use **Google Forms** to collect data from teachers (based on the structure from `Feedback Form.docx` and the `Resilience Screener`)
- The form includes:
  - Identification block: teacher ID, student ID, age, gender
  - Resilience screener: 27 items across 5 factors, scale 0 / 1 / 2 / NA
  - Feedback blocks (Blocks 1–11): acceptability, appropriateness, feasibility, usability, LLM agent evaluation, safety & ethics, intent to use, open-ended questions
- After submitting the form, the teacher should receive a response from the agent

---

### 2. Agent Knowledge Base

- The knowledge base is built exclusively from `references_toolkits_resilience_.docx`:
  - 5 resilience factors
  - For each factor: effective interventions, active ingredients, evidence base, open-access resources
- The knowledge base architecture must support **future expansion** without rewriting the core logic (e.g., adding new documents or rows)
- The agent **does not generate** recommendations from scratch — it responds solely based on the knowledge base

---

### 3. LLM Agent (Backend)

- Accepts structured data from the form: scores across 5 factors + open-text fields
- Generates a **resilience profile** for the student: low / medium / high level per factor
- Based on the profile, retrieves recommendations from the knowledge base
- Sends the response to the teacher (email or entry in Google Sheets)
- **Does not use** student names or any identifying information

---

### 4. Integration

- **Google Forms → backend:** via Google Apps Script (`onFormSubmit` trigger) or polling via the Google Sheets API
- **Backend → teacher:** email response via `GmailApp.sendEmail` or a record written to a linked Google Sheet
- The MVP **does not require** a separate web interface

---

### 5. System Constraints

- The system **does not produce diagnoses**
- Does not store or transmit any identifying student data
- Recommendations are advisory; final decisions remain with the teacher

---

## Task Plan

### Phase 1 — Backend & Knowledge Base

| # | Task |
|---|------|
| 1.1 | Prepare and structure the knowledge base from `references_toolkits_resilience_.docx` in a format suitable for RAG or prompt injection (JSON / vector DB / structured text) |
| 1.2 | Implement score interpretation logic: convert raw scores (0 / 1 / 2 / NA) per factor into a profile (low / medium / high), accounting for missing values |
| 1.3 | Design the LLM agent system prompt: role definition, constraints (no diagnoses, no stigmatizing language), instructions for knowledge base usage, response format |
| 1.4 | Implement an endpoint that accepts a JSON payload with form data and returns a structured agent response (profile + recommendations per factor) |
| 1.5 | Cover edge cases with basic tests: all NA, all 0, mixed scores |

---

### Phase 2 — Google Forms

| # | Task |
|---|------|
| 2.1 | Create the Google Form based on the resilience screener structure (27 items, scale 0 / 1 / 2 / NA, grouped by 5 factors) |
| 2.2 | Add feedback blocks (Blocks 1–11) — to be completed after all student assessments are done |
| 2.3 | Configure automatic response storage in Google Sheets |

---

### Phase 3 — Integration

*Below is a sample flow - it can be changed according to the architecture decisions in future

| # | Task |
|---|------|
| 3.1 | Write a Google Apps Script with an `onFormSubmit` trigger: parse form responses → POST request to the backend endpoint |
| 3.2 | Receive the agent response and deliver it to the teacher via email (`GmailApp.sendEmail`) or write it to a linked spreadsheet |
| 3.3 | Test the full cycle: form submission → backend processing → teacher response delivery |

---

### Phase 4 — Validation & Documentation

| # | Task |
|---|------|
| 4.1 | Run tests with multiple student profiles (various combinations of factor levels) |
| 4.2 | Review agent outputs: verify absence of stigmatizing language and alignment with the knowledge base |
| 4.3 | Document the procedure for extending the knowledge base (adding new sources) |

---

## Data Flow Diagram (MVP)

```
Teacher
  │
  ▼
Google Forms
  │  onFormSubmit
  ▼
Google Apps Script
  │  POST /analyze
  ▼
Backend (LLM Agent)
  │  ├── Score interpretation → profile across 5 factors
  │  └── RAG / prompt with knowledge base → recommendations
  │
  ▼
Email to teacher / Google Sheets
```

---

## 5 Resilience Factors — Item Map

| Factor | Screener Items |
|--------|----------------|
| Family Support | 3, 5, 11, 15, 18, 23 |
| Optimism | 1, 6, 12, 19, 24, 26 |
| Goal-Directedness / Coping | 2, 8, 13, 20, 25, 27 |
| Social Connections | 7, 9, 14, 16, 21 |
| Health | 4, 10, 17, 22 |