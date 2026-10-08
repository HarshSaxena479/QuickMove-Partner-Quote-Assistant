# QuickMove Partner Quote Assistant — Build Log

## 1. Project Overview

**Project:** QuickMove Partner Quote Assistant  
**Assignment:** AI Ops Engineer Take-Home  
**Selected Workflow:** Partner Information Intake, Normalization & Matching

### Problem

QuickMove operations teams receive partner quotes through unstructured channels such as WhatsApp, email, and text.

The same information can be written in many different ways, and manually comparing multiple quotes can result in:

- Missing information
- Inconsistent comparisons
- Budget mistakes
- Vehicle-size mistakes
- Extra follow-up work
- Slower vendor selection

### Goal

Build a practical tool that allows a QuickMove operations user to:

1. Enter customer requirements.
2. Paste one or more partner quotes.
3. Extract structured information using AI.
4. Identify missing information.
5. Validate requirements.
6. Compare multiple quotes.
7. Rank the available options.
8. Use AI recommendations as decision support.

The final vendor decision remains with the human QuickMove operations team.

---

# 2. Why I Chose This Workflow

The initial operations map identified three high-leverage automation opportunities:

1. Partner Information Intake, Normalization & Matching
2. Customer Relocation Control Tower
3. Exception Triage & Follow-Up Assistant

I selected **Partner Information Intake, Normalization & Matching** for the working build.

The workflow was a good fit for the time constraint because:

- Partner data is highly unstructured.
- AI can extract useful structure from free-form messages.
- Multiple quotes need to be compared consistently.
- Missing information can be surfaced automatically.
- Important business rules can be handled deterministically.
- The workflow can be turned into a usable tool without requiring a large backend.

I narrowed the scope to:

**QuickMove Partner Quote Assistant**

---

# 3. Initial Architecture

The initial design separated AI responsibilities from deterministic operational checks.

```text
Partner quote(s)
       ↓
AI extraction
       ↓
Structured quote JSON
       ↓
Deterministic validation
       ↓
Missing / ambiguous information
       ↓
Customer requirement comparison
       ↓
Quote ranking
       ↓
AI recommendation
       ↓
Human final decision