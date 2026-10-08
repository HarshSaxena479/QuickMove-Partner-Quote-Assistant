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
```
---  

# 4. Initial Build Setup

I built the solution as a lightweight Streamlit application so that the QuickMove operations team could use it without needing a separate engineering backend.

### Tools Used

- Python
- Streamlit
- Groq API
- `openai/gpt-oss-20b`
- python-dotenv
- Pandas
- PyCharm

### Initial Project Structure

```text
QuickMove/
├── .venv/
├── app.py
├── requirements.txt
├── README.md
└── .env
```
---

# 5. AI Extraction — First Iteration

The first AI component I built was the partner-quote extraction step.

The goal was to convert an unstructured partner message into a consistent structure that could be used by the rest of the application.

### Initial AI Prompt

I instructed the model to extract information from the partner quote and return structured JSON.

The extraction fields were:

- Vendor name
- Service type
- Move type
- Source location
- Destination
- Move date
- Price
- Packing
- Dismantling
- Reassembly
- Vehicle
- Availability
- Additional charges
- Missing information
- Notes

The model was instructed to return `"Unknown"` when information was not present and to identify missing information separately.

### Initial Design Decision

I deliberately used the LLM only for extracting and normalizing information from the free-form partner message.

I did not want the LLM to independently make all operational decisions. The extracted information would later be passed through deterministic validation rules for requirements such as budget, locations, packing, date, and vehicle size.

---

# 6. Iteration 1 — Multiple Quotes Caused a Parsing Error

During testing, I tested the application with multiple partner quotes.

The AI returned multiple extracted quotes as a JSON list instead of returning a single quote object for each input message.

The application code initially expected a dictionary and tried to access fields such as:

```python
quote["vendor_name"]
TypeError: list indices must be integers or slices, not str
What I Observed
The model had returned data in this general structure:
[
    {
        "vendor_name": "FastMove Logistics",
        ...
    },
    {
        "vendor_name": "CityShift Movers",
        ...
    }
]
The application, however, expected:
{
    "vendor_name": "FastMove Logistics",
    ...
}
```
How I Redirected the Implementation

Instead of assuming that the model would always return exactly one object, I changed the application logic to handle both possible valid structures:

A single extracted quote as a dictionary
Multiple extracted quotes as a list of dictionaries
The application now checks the returned type and adds each valid quote to the main quote collection.
This made the application more robust to variations in LLM output while keeping the downstream comparison logic unchanged.

Lesson
An LLM output should not be treated as perfectly deterministic, even when a JSON structure is requested.
The application therefore needs defensive parsing and validation around AI-generated output.

---

# 7. Iteration 2 — Improving Extraction Reliability

After the initial extraction worked, I tested the application with more realistic partner messages.

The tests showed that simply asking the model to extract fields was not enough. Partner messages could contain information in different formats, and the model could incorrectly mark information as missing or duplicate charges.

### Problems Identified

The extraction logic needed to handle:

- Information appearing later in a partner message
- Move dates expressed as days of the week
- Charges that were already represented by another field
- Additional charges that should not be counted twice
- Base price and additional charges separately
- Avoiding invented totals

### Changes to the Extraction Instructions

I strengthened the extraction instructions so that the model:

1. Reads the entire message before deciding that a field is missing.
2. Accepts a specific calendar date or a day of the week as a valid move date.
3. Does not mark the move date as missing when a day of the week is explicitly provided.
4. Does not count the same charge more than once.
5. Does not repeat charges already represented by fields such as reassembly, dismantling, or packing.
6. Keeps additional charges separate from the base price.
7. Does not calculate or invent a total price.
8. Extracts only information explicitly present in the partner message.

### Result

These changes made the extraction more reliable for realistic partner messages and reduced the chance of incorrect missing-information warnings and duplicate cost calculations.

This also reinforced the design principle that the AI should extract what is present in the source message rather than infer or invent operational information.

---

# 8. Iteration 3 — Adding Deterministic Validation

After improving the extraction step, I separated AI-based extraction from operational business-rule validation.

The reason was that some requirements should be checked consistently and predictably rather than being left entirely to the LLM.

### Deterministic Checks Added

The application validates the extracted quote against the customer's requirements for:

- Move type
- Source location
- Destination
- Move date
- Packing requirement
- Maximum budget
- Vehicle size

Each requirement is classified as:

- `match`
- `mismatch`
- `unknown`

### Location Normalization

Partner messages may use slightly different forms of the same location.

For example:

```text
Whitefield
Whitefield, Bengaluru
Whitefield, Bangalore

and

HSR
HSR Layout
HSR Layout, Bengaluru
HSR Layout, Bangalore
```
---

# 9. Iteration 4 — Making AI Recommendations Consistent With Validation

After adding deterministic validation, I used the validation results as inputs to the AI recommendation layer.

The purpose of the AI at this stage was not to independently decide whether a quote satisfied the requirements.

Instead, it was used to:

- Explain the validation results
- Summarize important concerns
- Identify missing information
- Provide a recommendation to the operations user

### Problem Identified

An LLM can sometimes interpret the same information differently from deterministic application logic.

For example, a vehicle requirement such as:

```text
Customer requires 16ft or larger
```
Design Change

I updated the AI recommendation instructions so that the deterministic validation results are treated as the source of truth.

The AI was explicitly instructed:

Do not contradict a deterministic match.
Do not describe a deterministic mismatch as satisfied.
Do not claim an unknown requirement is confirmed.
Do not invent additional charges.
Do not count the same charge twice.
Do not invent missing information.
Focus recommendations on genuine mismatches, missing information, and operational risks.
Final Responsibility Split

The system now separates responsibilities:

AI extraction

Understands unstructured partner messages.
Converts them into structured information.

Deterministic validation

Applies strict operational rules.
Determines match, mismatch, or unknown.

AI recommendation

Explains the results.
Highlights concerns and missing information.

QuickMove Ops

Makes the final vendor-selection decision.

This creates a human-in-the-loop workflow rather than allowing the AI to make an unchecked operational decision.
---

# 10. Testing and Edge Cases

After implementing extraction, validation, and comparison, I tested the application with multiple operational scenarios.

## Test 1 — Multiple Valid Quotes

### Customer Requirements

```text
Move type: 2BHK
Source: Whitefield
Destination: HSR
Preferred date: Sunday
Maximum budget: ₹10,000
Packing: Yes
Vehicle: 16ft or larger
```
Quote1 - FastMove Logistics
```2BHK move from Whitefield to HSR on Sunday.
Packing included.
Base price: ₹8,500.
16ft vehicle available.
Dismantling included.
Reassembly: ₹500.
Move availability confirmed for Sunday.
```
Result
```
The quote was identified as a complete match.

Match score: 100/100
Known cost: ₹9,000
All deterministic requirements matched.
```

Quote 2 — CityShift Movers
```2BHK move from Whitefield to HSR on Sunday.
Packing included.
Base price: ₹9,200.
16ft vehicle available.
Reassembly: ₹500.
Dismantling will be confirmed later.
Move available on Sunday.
```
Result
```
The quote also matched the explicit customer requirements.

However, the application identified dismantling as information that still needed confirmation.

Match score: 100/100
Known cost: ₹9,700
Dismantling information required confirmation.

The ranking placed FastMove first because both quotes satisfied the requirements but FastMove had the lower known cost.
```
---

# 11. Final Product Design

After testing the core workflow, I focused on making the application practical for a non-technical QuickMove operations user.

### Final Workflow

The user can:

1. Enter customer relocation requirements.
2. Paste one or more partner quotes.
3. Extract structured information from the quotes.
4. Review missing information.
5. Review deterministic requirement validation.
6. Compare multiple quotes.
7. See a ranked list of available options.
8. Review AI-generated recommendations.
9. Make the final vendor-selection decision.

### Human-in-the-Loop

The application does not automatically book a vendor.

AI is used to reduce manual work and provide decision support, while the QuickMove operations team remains responsible for the final decision.

This is important because partner quotes may contain incomplete or ambiguous information, and the cost of an incorrect operational decision can be significant.

### Ranking Logic

Quotes are ranked using deterministic requirement matching and known cost.

The system prioritizes:

1. Higher requirement-match score.
2. Lower known cost when match scores are equal.

The ranking is intended to help the operations team review options faster rather than automatically selecting a vendor.

---

# 12. Reliability and Failure Handling

Because the application depends on an LLM, I added defensive handling around AI output.

The application accounts for cases such as:

- Invalid JSON responses
- Unexpected list/dictionary output
- Missing fields
- Unknown information
- Ambiguous partner messages
- Missing vendor information
- Missing vehicle information
- Missing availability
- Conflicting customer requirements
- Explicit budget mismatches
- Vehicle-size mismatches

If the AI response cannot be parsed reliably, the application falls back to a safe state rather than presenting an unreliable recommendation as a confirmed decision.

---

# 13. Current Limitations

The current version intentionally focuses on the partner-quote workflow rather than attempting to automate the entire QuickMove operation.

Current limitations include:

- Partner quotes are entered manually by the operations user.
- The application does not directly connect to WhatsApp or email.
- The application does not automatically contact partners for missing information.
- Location normalization currently covers a limited set of known variations.
- Cost calculation only uses explicitly known costs.
- The system does not automatically book the selected vendor.
- Human review is still required before a final booking decision.

These limitations were intentional because the goal was to build a focused, usable workflow within the assignment's time constraint rather than create a large production system.

---

# 14. Future Improvements

If this were developed further, the next improvements would include:

1. Direct WhatsApp/email ingestion for partner messages.
2. A persistent database of partner quotes and historical pricing.
3. City-specific partner and pricing rules.
4. Automatic follow-up messages for missing information.
5. Partner reliability and historical-performance scoring.
6. Integration with QuickMove's customer relocation control tower.
7. Audit logs for every AI extraction and operational decision.
8. Automated evaluation datasets for measuring extraction accuracy.
9. Authentication and role-based access for operations users.
10. Monitoring for AI extraction failures and unusual outputs.

The current architecture was designed so these capabilities could be added later without changing the core separation between AI extraction, deterministic validation, AI decision support, and human approval.

---

# 16. Actual Build Time

The build was completed across two working sessions.

### Session 1
- Start: 6:00 PM
- End: 12:30 AM
- Active work time: approximately 6.5 hours

### Session 2
- Start: 8:00 AM
- End: 12:30 PM
- Active work time: approximately 4.5 hours

### Total Active Build Time

Approximately **11 hours** across the two sessions.

The times above reflect the actual time spent working on the assignment.