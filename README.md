# QuickMove Partner Quote Assistant

An AI-assisted operations tool for QuickMove that converts messy moving-partner quotes into structured information and compares them against customer requirements.

## 🚀 Live Demo

**[Open QuickMove Partner Quote Assistant](https://harshsaxena479-quickmove-partner-quote-assistant-app-w8ofxg.streamlit.app/)**

## Problem

QuickMove operations teams receive partner information in unstructured formats such as WhatsApp messages, emails, and text.

Manually reading and comparing multiple partner quotes can lead to:

- Missing important information
- Inconsistent comparisons
- Budget or vehicle-size mistakes
- Time-consuming follow-ups
- Difficulty deciding which quote is the best fit

## Solution

The QuickMove Partner Quote Assistant helps operations teams analyze partner quotes in a consistent way.

The workflow is:

Partner quote(s)
→ AI extraction
→ Structured quote information
→ Deterministic requirement validation
→ Missing information detection
→ Quote comparison
→ Ranking
→ Human final decision

The system uses AI for extracting and interpreting unstructured partner messages, while deterministic Python checks are used for important requirement validation.

The final vendor selection remains with the QuickMove operations team.

## Features

- Extracts structured information from messy partner quotes
- Supports multiple partner quotes
- Detects missing information
- Compares quotes against customer requirements
- Validates:
  - Move type
  - Source location
  - Destination
  - Move date
  - Packing requirement
  - Maximum budget
  - Vehicle size
- Handles common location variations such as HSR and HSR Layout
- Calculates known cost from base price and explicitly stated reassembly cost
- Detects requirement mismatches
- Ranks multiple quotes
- Shows why a quote ranks higher or lower
- Keeps a human operator in the decision loop

## Screenshots

### 1. Main Interface

The operations user enters customer requirements and pastes one or more partner quotes.

![QuickMove Partner Quote Assistant - Main Interface](screenshots/main-interface.png)

### 2. Extracted Partner Information

The assistant converts unstructured partner messages into structured quote information and highlights information that needs to be confirmed.

![Extracted Partner Information](screenshots/extracted-information.png)

### 3. Requirement Validation

Each partner quote is checked against the customer's requirements using deterministic validation.

![Requirement Validation](screenshots/requirement-validation1.png)
![Requirement Validation](screenshots/requirement-validation2.png)
![Requirement Validation](screenshots/requirement-validation3.png)

### 4. Quote Comparison

Multiple partner quotes are ranked using requirement matching and known cost, helping the operations team identify the strongest option.

![Quote Comparison](screenshots/quote-comparison.png)
## Tech Stack Used

- Python 3.10.1
- Streamlit
- Groq API
- OpenAI GPT-OSS-20B
- python-dotenv

## Project Structure

```text
QuickMove/
│
├── app.py
├── screenshots
    ├── main-interface.png
    ├── extracted-information.png
    ├── requirement-validation1.png
    ├── requirement-validation2.png
    ├── requirement-validation3.png
    └── quote-comparison.png
├── requirements.txt
├── README.md
├── .env
└── .venv/
```
## How to Use (Input Guide)
### Customer Requirements

Enter the customer's requirements using the following fields:

- **Move Type:** Enter the type of move, for example `2BHK`.
- **Source Location:** Enter the pickup location, for example `Whitefield`.
- **Destination:** Enter the delivery location, for example `HSR`.
- **Preferred Move Date:** Enter a specific date or a day of the week, for example `Sunday`.
- **Maximum Budget:** Enter the customer's maximum budget in INR, for example `10000`.
- **Packing Required:** Select `Yes` if the customer requires packing, otherwise select `No`.
- **Vehicle Preference:** Enter the minimum required vehicle size, for example `16ft`.

### Partner Quotes

Paste the partner's quote exactly as received from WhatsApp, email, or another source.

For example:

```text
Vendor: FastMove Logistics

We can handle your 2BHK household move from Whitefield, Bengaluru
to HSR Layout, Bengaluru on Sunday.

Packing is included.
Dismantling is included.
Reassembly is ₹500.
A 16ft vehicle is available.
Move availability is confirmed for Sunday.

Base price: ₹8,500.
Reassembly: ₹500.
```