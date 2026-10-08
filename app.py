import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# -----------------------------
# Configuration
# -----------------------------

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY not found. Please check your .env file.")
    st.stop()

client = Groq(api_key=api_key)

# -----------------------------
# AI Extraction
# -----------------------------

def extract_partner_quote(message):

    prompt = f"""
You are an operations assistant for QuickMove, a relocation company.

Your job is to extract structured information from a property or moving
partner's message.

IMPORTANT RULES:
1. Extract only information explicitly present in the message.
2. Never guess or invent missing information.
3. If information is missing, use "Unknown".
4. Identify important missing information in the "missing_information" field.
5. Return ONLY valid JSON.
6. Do not include markdown or explanations outside the JSON.
7. If the message says "shifting", "moving", "relocation", or similar wording,
   classify the service as "Moving".
8. If the message contains "1BHK", "2BHK", "3BHK", etc., extract that as
   the move_type even if it appears directly before the word "shifting".
9. Read the entire message before deciding that a field is missing.
10. A move date may be provided as a specific calendar date OR as a day of
    the week such as Monday, Tuesday, Sunday, etc. If a day of the week is
    explicitly stated, extract it as move_date and do not mark the date as
    missing.
11. Do not mark "Exact Move Date" as missing when a day of the week is
    explicitly provided as the move_date.
12. Do not count the same charge more than once.
13. If a specific charge is already extracted into a field such as reassembly,
    dismantling, or packing, do not repeat that same amount in additional_charges.
14. additional_charges should contain only charges that are explicitly separate
    from the main price and are not already represented by another field.
15. Never calculate or invent a total price. Extract the base price and each
    explicitly stated additional charge separately.

Return exactly this JSON structure:

{{
    "vendor_name": "",
    "service_type": "",
    "move_type": "",
    "source_location": "",
    "destination": "",
    "move_date": "",
    "price": "",
    "packing": "",
    "dismantling": "",
    "reassembly": "",
    "vehicle": "",
    "availability": "",
    "additional_charges": "",
    "missing_information": [],
    "notes": ""
}}

Partner message:
{message}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        return {
            "error": "AI returned invalid JSON",
            "raw_response": result
        }

def normalize_location(location):
    location = str(location).strip().lower()

    # Normalize common location naming variations
    replacements = {
        "hsr layout": "hsr",
        "hsr layout, bangalore": "hsr",
        "hsr layout, bengaluru": "hsr",
        "whitefield": "whitefield",
        "whitefield, bangalore": "whitefield",
        "whitefield, bengaluru": "whitefield",
    }

    return replacements.get(location, location)
# -----------------------------
# Compare Quote With Requirements
# -----------------------------
def calculate_known_cost(quote):
    try:
        price_text = str(quote.get("price", ""))
        price_digits = "".join(
            c for c in price_text
            if c.isdigit()
        )

        base_price = int(price_digits) if price_digits else None

        reassembly_text = str(
            quote.get("reassembly", "")
        )

        reassembly_digits = "".join(
            c for c in reassembly_text
            if c.isdigit()
        )

        reassembly_cost = (
            int(reassembly_digits)
            if reassembly_digits
            else 0
        )

        if base_price is None:
            return None

        return base_price + reassembly_cost

    except Exception:
        return None
def validate_quote(quote, requirements):
    checks = []

    # 1. Move type
    if quote.get("move_type") and requirements.get("move_type"):
        checks.append({
            "requirement": "move_type",
            "status": "match" if quote["move_type"].strip().lower() == requirements["move_type"].strip().lower() else "mismatch",
            "customer_value": requirements["move_type"],
            "quote_value": quote["move_type"]
        })

    # 2. Source location
    if quote.get("source_location") and requirements.get("source_location"):
        checks.append({
            "requirement": "source_location",
            "status": "match" if normalize_location(quote["source_location"]) == normalize_location(requirements["source_location"]) else "mismatch",
            "customer_value": requirements["source_location"],
            "quote_value": quote["source_location"]
        })

    # 3. Destination
    if quote.get("destination") and requirements.get("destination"):
        checks.append({
            "requirement": "destination",
            "status": "match" if normalize_location(quote["destination"]) == normalize_location(requirements["destination"]) else "mismatch",
            "customer_value": requirements["destination"],
            "quote_value": quote["destination"]
        })

    # 4. Move date
    if quote.get("move_date") and requirements.get("move_date"):
        checks.append({
            "requirement": "move_date",
            "status": "match" if quote["move_date"].strip().lower() == requirements["move_date"].strip().lower() else "mismatch",
            "customer_value": requirements["move_date"],
            "quote_value": quote["move_date"]
        })

    # 5. Packing
    if requirements.get("packing_required") != "Not specified":

        packing_required = str(
            requirements["packing_required"]
        ).lower().strip()

        packing_quote = str(
            quote.get("packing", "")
        ).lower().strip()

        if packing_required == "yes":

            if "not included" in packing_quote:
                status = "mismatch"

            elif "included" in packing_quote:
                status = "match"

            else:
                status = "unknown"

        elif packing_required == "no":

            if (
                    "not included" in packing_quote
                    or packing_quote == "no"
            ):
                status = "match"

            elif "included" in packing_quote:
                status = "mismatch"

            else:
                status = "unknown"

        else:
            status = "unknown"

        checks.append({
            "requirement": "packing_required",
            "status": status,
            "customer_value": requirements[
                "packing_required"
            ],
            "quote_value": quote.get(
                "packing",
                "Unknown"
            )
        })

    # 6. Budget
    try:
        total_known_cost = calculate_known_cost(quote)

        budget = float(
            requirements.get("maximum_budget", 0)
        )

        if total_known_cost is not None:
            checks.append({
                "requirement": "maximum_budget",
                "status": (
                    "match"
                    if total_known_cost <= budget
                    else "mismatch"
                ),
                "customer_value": budget,
                "quote_value": total_known_cost
            })

    except Exception:
        checks.append({
            "requirement": "maximum_budget",
            "status": "unknown",
            "customer_value": requirements.get(
                "maximum_budget"
            ),
            "quote_value": "Unknown"
        })

    # 7. Vehicle size
    try:
        vehicle_text = str(
            quote.get("vehicle", "")
        )

        vehicle_numbers = "".join(
            c if c.isdigit() else " "
            for c in vehicle_text
        ).split()

        quote_vehicle_size = (
            int(vehicle_numbers[0])
            if vehicle_numbers
            else None
        )

        preference_text = str(
            requirements.get(
                "vehicle_preference",
                ""
            )
        )

        preference_numbers = "".join(
            c if c.isdigit() else " "
            for c in preference_text
        ).split()

        required_vehicle_size = (
            int(preference_numbers[0])
            if preference_numbers
            else None
        )

        if (
                quote_vehicle_size is not None
                and required_vehicle_size is not None
        ):

            checks.append({
                "requirement": "vehicle_preference",
                "status": (
                    "match"
                    if quote_vehicle_size >= required_vehicle_size
                    else "mismatch"
                ),
                "customer_value": requirements[
                    "vehicle_preference"
                ],
                "quote_value": quote["vehicle"]
            })

        else:

            checks.append({
                "requirement": "vehicle_preference",
                "status": "unknown",
                "customer_value": requirements.get(
                    "vehicle_preference"
                ),
                "quote_value": quote.get(
                    "vehicle",
                    "Unknown"
                )
            })

    except Exception:

        checks.append({
            "requirement": "vehicle_preference",
            "status": "unknown",
            "customer_value": requirements.get(
                "vehicle_preference"
            ),
            "quote_value": quote.get(
                "vehicle",
                "Unknown"
            )
        })

    return checks
def compare_quote(quote,requirements,validation_checks):

    prompt = f"""
You are an operations decision-support assistant for QuickMove.

Compare a moving partner's quote against the customer's requirements.

IMPORTANT RULES:
1. Do not invent information.
2. If the quote does not contain enough information to determine a match,
   mark it as "Unknown".
3. Clearly distinguish between a confirmed match and an assumption.
4. The human QuickMove operator makes the final decision.
5. Return ONLY valid JSON.
6. "match_score" MUST be an integer between 0 and 100.
7. Never return a decimal for match_score.
8. Evaluate every customer requirement individually.
9. Only call something a match when the quote provides evidence for it.
10. Compare each customer requirement against the extracted quote information.
11. Never change, reinterpret, or invent a customer requirement.
12. For move_date, compare the dates/words exactly. If both say Sunday, it is a match.
13. For locations, allow common naming variations. For example, "HSR" and "HSR Layout" should be treated as the same location.
14. Treat the deterministic validation checks provided below as the source of truth for requirement match/mismatch/unknown status.
15. Do not contradict the deterministic validation checks. If a check says "match", do not describe that requirement as a mismatch or concern. If a check says "mismatch", do not describe it as satisfied. If a check says "unknown", do not claim that the requirement is confirmed.
16. For vehicle preference, understand size requirements numerically. A 15ft vehicle does NOT satisfy a requirement of 16ft or larger.
17. For budget, use the base price plus explicitly stated additional charges. Do not count the same charge twice.
18. If base price is ₹9,200 and reassembly is ₹500, the known total is ₹9,700.
19. Do not treat an explicitly stated additional charge as unknown.
20. Do not invent additional charges that are not present in the quote.
21. A missing vendor name is a concern, but it should not cause unrelated requirements such as date, destination, or budget to be marked as mismatches.
22. Focus the recommendation on genuine mismatches, missing information, and operational risks.

Customer requirements:

{json.dumps(requirements, indent=2)}

Partner quote:

{json.dumps(quote, indent=2)}

Deterministic validation checks:

{json.dumps(validation_checks, indent=2)}

Return exactly this structure:

{{
    "overall_result": "Good Match / Partial Match / Poor Match / Cannot Determine",
    "match_score": 0,
    "matches": [],
    "concerns": [],
    "missing_information": [],
    "recommendation": ""
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    try:

        parsed_result = json.loads(result)

        # Validate the expected structure
        required_fields = [
            "overall_result",
            "match_score",
            "matches",
            "concerns",
            "missing_information",
            "recommendation"
        ]

        if not all(
                field in parsed_result
                for field in required_fields
        ):
            raise ValueError(
                "Missing required fields in AI response"
            )

        # Ensure match_score is an integer
        parsed_result["match_score"] = int(
            parsed_result["match_score"]
        )

        # Keep score within valid range
        parsed_result["match_score"] = max(
            0,
            min(
                100,
                parsed_result["match_score"]
            )
        )

        return parsed_result

    except (json.JSONDecodeError, ValueError, TypeError):

        return {
            "error": "AI comparison could not be parsed safely.",
            "raw_response": result,
            "overall_result": "Cannot Determine",
            "match_score": 0,
            "matches": [],
            "concerns": [
                "AI comparison response was incomplete or invalid."
            ],
            "missing_information": [],
            "recommendation": (
                "Use the deterministic requirement checks "
                "above to make the decision. AI recommendation "
                "is unavailable for this quote."
            )
        }


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="QuickMove Partner Quote Assistant",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 QuickMove Partner Quote Assistant")

st.write(
    "Convert messy partner quotes into structured information "
    "and compare them against customer requirements."
)

st.info(
    "How it works: AI extracts quote details → deterministic checks "
    "validate customer requirements → quotes are ranked by match "
    "and known cost → QuickMove Ops makes the final decision."
)


st.divider()


# -----------------------------
# Customer Requirements
# -----------------------------

st.subheader("1. Customer Requirements")

col1, col2 = st.columns(2)

with col1:

    move_type = st.text_input(
        "Move type",
        placeholder="Example: 2BHK"
    )

    source_location = st.text_input(
        "Source location",
        placeholder="Example: Whitefield"
    )

    destination = st.text_input(
        "Destination",
        placeholder="Example: HSR"
    )

    move_date = st.text_input(
        "Preferred move date",
        placeholder="Example: Sunday"
    )

with col2:

    budget = st.number_input(
        "Maximum budget (₹)",
        min_value=0,
        value=10000,
        step=500
    )

    packing_required = st.selectbox(
        "Packing required?",
        ["Yes", "No", "Not specified"]
    )

    vehicle_preference = st.text_input(
        "Vehicle preference",
        placeholder="Example: 16ft or larger"
    )


# -----------------------------
# Partner Quote
# -----------------------------

st.subheader("2. Partner Quotes")

partner_message = st.text_area(
    "Paste partner quote(s)",
    height=260,
    placeholder=(
        "Paste one or more partner quotes here.\n\n"
        "For multiple quotes, separate each quote with:\n"
        "---QUOTE---\n\n"
        "Example:\n"
        "Vendor A: 2BHK shifting from Whitefield to HSR on Sunday. "
        "Packing included. ₹8,500. 16ft vehicle available.\n\n"
        "---QUOTE---\n\n"
        "Vendor B: 2BHK shifting from Whitefield to HSR on Sunday. "
        "Packing included. ₹9,200. 15ft vehicle available."
    )
)


# -----------------------------
# Analyze Button
# -----------------------------

analyze_button = st.button(
    "🔍 Analyze & Compare",
    type="primary"
)


if analyze_button:

    if not partner_message.strip():

        st.warning("Please paste a partner message first.")

    else:

        requirements = {
            "move_type": move_type,
            "source_location": source_location,
            "destination": destination,
            "move_date": move_date,
            "maximum_budget": budget,
            "packing_required": packing_required,
            "vehicle_preference": vehicle_preference
        }

        with st.spinner("Analyzing partner quote(s)..."):

            partner_quotes = [
                quote.strip()
                for quote in partner_message.split("---QUOTE---")
                if quote.strip()
            ]

            quotes = []

            for message in partner_quotes:
                extracted_quote = extract_partner_quote(message)

                if "error" not in extracted_quote:
                    quotes.append(extracted_quote)

        if not quotes:

            st.error("Could not analyze any partner quotes.")

        else:

            st.success(
                f"{len(quotes)} partner quote(s) successfully analyzed!"
            )

            # -----------------------------
            # Extracted Information
            # -----------------------------

            st.divider()

            # -----------------------------
            # Extracted Information
            # -----------------------------

            st.divider()

            st.subheader("3. Extracted Information")

            for index, quote in enumerate(quotes, start=1):
                st.markdown(f"### Partner Quote {index}")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Vendor Name**")
                    st.write(quote["vendor_name"])

                    st.write("**Service Type**")
                    st.write(quote["service_type"])

                    st.write("**Move Type**")
                    st.write(quote["move_type"])

                    st.write("**Source Location**")
                    st.write(quote["source_location"])

                    st.write("**Destination**")
                    st.write(quote["destination"])

                    st.write("**Move Date**")
                    st.write(quote["move_date"])

                    st.write("**Price**")
                    st.write(quote["price"])

                with col2:
                    st.write("**Packing**")
                    st.write(quote["packing"])

                    st.write("**Dismantling**")
                    st.write(quote["dismantling"])

                    st.write("**Reassembly**")
                    st.write(quote["reassembly"])

                    st.write("**Vehicle**")
                    st.write(quote["vehicle"])

                    st.write("**Availability**")
                    st.write(quote["availability"])

                    st.write("**Other Additional Charges**")
                    st.write(
                        quote["additional_charges"]
                        if quote["additional_charges"]
                        else "None identified"
                    )
            # -----------------------------
            # Missing Information
            # -----------------------------

            st.divider()

            st.subheader("4. Information to Confirm Before Booking")

            has_missing_information = False

            for index, quote in enumerate(quotes, start=1):

                missing = quote.get(
                    "missing_information",
                    []
                )

                if missing:

                    has_missing_information = True

                    st.markdown(
                        f"**Partner Quote {index}**"
                    )

                    for item in missing:
                        label = item.replace(
                            "_",
                            " "
                        ).title()

                        st.warning(
                            f"⚠️ {label}"
                        )

            if not has_missing_information:
                st.success(
                    "No important missing information detected."
                )
            # -----------------------------
            # Comparison
            # -----------------------------

            st.divider()

            st.subheader("5. Customer Requirement Comparison")

            with st.spinner("Comparing partner quotes with customer requirements..."):

                comparisons = []

                for quote in quotes:
                    validation_checks = validate_quote(
                        quote,
                        requirements
                    )

                    comparison = compare_quote(
                        quote,
                        requirements,
                        validation_checks
                    )

                    comparisons.append({
                        "quote": quote,
                        "validation_checks": validation_checks,
                        "comparison": comparison
                    })

            # Display comparison results for each partner quote

            for index, item in enumerate(comparisons, start=1):

                quote = item["quote"]
                validation_checks = item["validation_checks"]
                comparison = item["comparison"]

                st.divider()

                st.subheader(f"Partner Quote {index}")

                if "error" in comparison:
                    st.error(comparison["error"])

                    st.code(
                        comparison.get("raw_response", ""),
                        language="text"
                    )

                    continue

                # Count deterministic validation results
                matched_checks = [
                    check for check in validation_checks
                    if check["status"] == "match"
                ]

                mismatched_checks = [
                    check for check in validation_checks
                    if check["status"] == "mismatch"
                ]

                unknown_checks = [
                    check for check in validation_checks
                    if check["status"] == "unknown"
                ]

                total_checks = len(validation_checks)

                # Calculate score using deterministic checks
                if total_checks > 0:
                    score = round(
                        (len(matched_checks) / total_checks) * 100
                    )
                else:
                    score = 0

                # Determine overall result
                if mismatched_checks:
                    result = "Partial Match"

                elif unknown_checks:
                    result = "Cannot Determine"

                else:
                    result = "Good Match"

                st.write(
                    f"### {result}"
                )

                st.metric(
                    "Match Score",
                    f"{score}/100"
                )

                st.write("**Requirement Checks**")

                for check in validation_checks:

                    requirement = check["requirement"]
                    customer_value = check["customer_value"]
                    quote_value = check["quote_value"]
                    status = check["status"]

                    labels = {
                        "move_type": "Move type",
                        "source_location": "Source",
                        "destination": "Destination",
                        "move_date": "Move date",
                        "maximum_budget": "Budget",
                        "packing_required": "Packing",
                        "vehicle_preference": "Vehicle"
                    }

                    label = labels.get(
                        requirement,
                        requirement.replace("_", " ").title()
                    )

                    if status == "match":

                        st.success(
                            f"✓ {label}: {quote_value}"
                        )

                    elif status == "mismatch":

                        st.error(
                            f"✗ {label}: Customer requires "
                            f"{customer_value}, quote says {quote_value}"
                        )

                    else:

                        st.warning(
                            f"? {label}: Could not determine"
                        )

                col1, col2 = st.columns(2)

                with col1:

                    st.write("**Decision Summary**")

                    if mismatched_checks:

                        st.write("**Concerns**")

                        for check in mismatched_checks:
                            requirement = check["requirement"]

                            labels = {
                                "move_type": "Move type",
                                "source_location": "Source",
                                "destination": "Destination",
                                "move_date": "Move date",
                                "maximum_budget": "Budget",
                                "packing_required": "Packing",
                                "vehicle_preference": "Vehicle"
                            }

                            label = labels.get(
                                requirement,
                                requirement.replace("_", " ").title()
                            )

                            st.error(
                                f"✗ {label}: Customer requires "
                                f"{check['customer_value']}, "
                                f"quote says {check['quote_value']}"
                            )

                    if unknown_checks:

                        st.write("**Information Needed Before Decision**")

                        for check in unknown_checks:
                            st.warning(
                                f"? {check['requirement'].replace('_', ' ').title()} "
                                f"could not be determined"
                            )

                    if not mismatched_checks and not unknown_checks:
                        st.success(
                            "✓ Quote satisfies all checked customer requirements."
                        )

                st.write("**AI Recommendation**")

                st.info(
                    comparison.get(
                        "recommendation",
                        "No recommendation available."
                    )
                )

                st.caption(
                    "AI output is decision support only. "
                    "Final vendor selection remains with QuickMove Ops."
                )
            # -----------------------------
            # Quote Comparison Summary
            # -----------------------------

            st.divider()

            st.subheader("6. Quote Comparison Summary")

            ranked_quotes = []

            for index, item in enumerate(comparisons, start=1):

                quote = item["quote"]
                validation_checks = item["validation_checks"]

                matched_checks = [
                    check for check in validation_checks
                    if check["status"] == "match"
                ]

                mismatched_checks = [
                    check for check in validation_checks
                    if check["status"] == "mismatch"
                ]

                unknown_checks = [
                    check for check in validation_checks
                    if check["status"] == "unknown"
                ]

                total_checks = len(validation_checks)

                if total_checks > 0:
                    score = round(
                        (len(matched_checks) / total_checks) * 100
                    )
                else:
                    score = 0

                known_cost = calculate_known_cost(quote)

                ranked_quotes.append({
                    "quote_number": index,
                    "vendor": quote.get(
                        "vendor_name",
                        "Unknown"
                    ),
                    "score": score,
                    "known_cost": known_cost,
                    "vehicle": quote.get(
                        "vehicle",
                        "Unknown"
                    ),
                    "mismatches": len(mismatched_checks),
                    "unknowns": len(unknown_checks)
                })

            # Sort by match score first,
            # then by known cost
            ranked_quotes.sort(
                key=lambda x: (
                    -x["score"],
                    x["known_cost"]
                    if x["known_cost"] is not None
                    else float("inf")
                )
            )

            for rank, item in enumerate(
                    ranked_quotes,
                    start=1
            ):

                if rank == 1:

                    st.markdown("### 🥇 Best Match")

                else:

                    st.markdown(
                        f"### Option {rank}"
                    )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write("**Quote**")

                    st.write(
                        f"Partner Quote {item['quote_number']}"
                    )

                with col2:

                    st.write("**Match Score**")

                    st.write(
                        f"{item['score']}/100"
                    )

                with col3:

                    st.write("**Known Cost**")

                    if item["known_cost"] is not None:

                        st.write(
                            f"₹{item['known_cost']:,}"
                        )

                    else:

                        st.write("Unknown")

                with col4:

                    st.write("**Vehicle**")

                    st.write(
                        item["vehicle"]
                    )

                if item["mismatches"] > 0:

                    st.warning(
                        f"{item['mismatches']} requirement(s) "
                        f"not satisfied."
                    )

                    st.caption(
                        f"Why this ranks here: "
                        f"{item['mismatches']} requirement(s) "
                        f"not satisfied."
                    )

                elif item["unknowns"] > 0:

                    st.warning(
                        f"{item['unknowns']} requirement(s) "
                        f"could not be determined."
                    )

                    st.caption(
                        f"Why this ranks here: "
                        f"{item['unknowns']} requirement(s) "
                        f"could not be determined."
                    )

                else:

                    st.success(
                        "All checked customer requirements are satisfied."
                    )

                    if rank == 1:

                        st.caption(
                            "Why this ranks here: all requirements matched "
                            "and this quote has the lowest known cost."
                        )

                    else:

                        st.caption(
                            "Why this ranks here: all requirements matched, "
                            "but another quote has a lower known cost."
                        )

            st.caption(
                "Ranking is based on deterministic requirement matching "
                "and known cost. Final vendor selection remains with "
                "QuickMove Ops."
            )