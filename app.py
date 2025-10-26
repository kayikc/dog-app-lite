import requests
import pandas as pd
import streamlit as st

# Define the colors from the image (min/blue to max/red)
TITLE_COLORS = ["#4285F4", "#42A5F5", "#34A853", "#FBBC05", "#F29900", "#EA4335"]

# --------------------
# Custom Styling for Google Look
# --------------------
custom_css = f"""
<style>
/* Center the main content column and limit its width */
.css-18e3th9 {{
    padding-top: 10rem; /* Pushes content further down the page */
    max-width: 600px; /* Limits the max width of the center content */
}}

/* Hide default Streamlit header/footer/menu */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* Style for the 'DogDog Go' Title */
.dogdog-go-title {{
    font-size: 5rem; /* Larger font size */
    font-weight: bold;
    text-align: center;
    margin-bottom: 2rem;
    line-height: 1.2;
}}

/* Style for the colored letters */
{' '.join([f'.color-{i+1} {{ color: {color}; }}' for i, color in enumerate(TITLE_COLORS)])}

/* Style the search box to be centered and rounded */
.stTextInput > div > div > input {{
    border-radius: 24px;
    height: 48px;
    padding: 0 20px;
    font-size: 16px;
    box-shadow: 0 1px 6px rgba(32,33,36,.28);
    border-color: transparent !important; /* Remove default border */
    transition: box-shadow 300ms ease-in-out;
}}

.stTextInput > div > div > input:focus {{
    box-shadow: 0 1px 8px rgba(32,33,36,.38); /* Subtle lift on focus */
}}
</style>
"""

# Inject the custom CSS
st.markdown(custom_css, unsafe_allow_html=True)


# --------------------
# Page config
# --------------------
st.set_page_config(page_title="DogDog Go", page_icon="🐾", layout="centered")

# --------------------
# Google Landing Page UI: Title
# --------------------

# DogDog Go Title with Colored Letters
title_html = """
<div class="dogdog-go-title">
    <span class="color-1">D</span><span class="color-2">o</span><span class="color-3">g</span>
    <span class="color-4">D</span><span class="color-5">o</span><span class="color-6">g</span>
    <span class="color-1">G</span><span class="color-2">o</span>
</div>
"""
st.markdown(title_html, unsafe_allow_html=True)

# --------------------
# Helpers
# --------------------


@st.cache_data(show_spinner=False)
def load_breeds():
    """
    Fetch all dog breeds from TheDogAPI.
    Returns a pandas DataFrame with clean columns.
    This does not require an API key for basic usage.
    """
    url = "https://api.thedogapi.com/v1/breeds"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # normalise into a DataFrame
    df = pd.json_normalize(data)

    # we'll keep just the columns we care about
    keep_cols = [
        "name",
        "bred_for",
        "breed_group",
        "origin",
        "life_span",
        "temperament",
        "weight.metric",
        "height.metric",
        "image.url",
        "id",
    ]

    # Some columns may not exist for all breeds, so fill missing
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None

    df = df[keep_cols].rename(
        columns={
            "name": "Name",
            "bred_for": "BredFor",
            "breed_group": "Group",
            "origin": "Origin",
            "life_span": "LifeSpan",
            "temperament": "Temperament",
            "weight.metric": "WeightKg",
            "height.metric": "HeightCm",
            "image.url": "ImageURL",
            "id": "BreedID",
        }
    )

    return df


def find_matches(df, query_text):
    """
    Return all rows whose Name contains the query.
    Case-insensitive, partial match.
    """
    if not query_text:
        return pd.DataFrame()  # empty
    mask = df["Name"].str.contains(query_text, case=False, na=False)
    return df[mask].reset_index(drop=True)


def parse_range(text_val):
    """
    Many fields are in the form "20 - 30".
    We'll just return the first number so we can show a simple metric.
    If it's empty or malformed, return '—'.
    """
    if not text_val or not isinstance(text_val, str):
        return "—"

    parts = text_val.split("-")
    first = parts[0].strip()
    if first:
        return first
    return "—"


# --------------------
# Load data once
# --------------------
with st.spinner("Fetching breed data..."):
    breeds_df = load_breeds()


# --------------------
# UI: search box
# --------------------
# The search box is the main element below the title, styled by the CSS.
breed_query = st.text_input(
    "",  # No label
    placeholder="Search for a dog breed, try husky...",
).strip()

results_df = find_matches(breeds_df, breed_query)


# --------------------
# Main result display
# --------------------
if breed_query:
    st.markdown("---")  # Add a separator for results
    if results_df.empty:
        st.warning("No match found.")
    else:
        # If multiple results, let user pick one from a dropdown
        names = results_df["Name"].tolist()

        selected_name = st.selectbox(
            "Select a breed:",
            options=names,
            index=0,
        )

        row = results_df[results_df["Name"] == selected_name].iloc[0]

        info_tab, img_tab = st.tabs([" Info", " Photo"])

        with info_tab:
            st.subheader(row["Name"])

            # Optional short blurb
            if row["BredFor"]:
                st.markdown(f"**Bred for:** {row['BredFor']}")
            if row["Temperament"]:
                st.markdown(f"**Temperament:** {row['Temperament']}")

            # 3 metrics in a row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Weight (kg)", parse_range(row["WeightKg"]))
            with col2:
                st.metric("Height (cm)", parse_range(row["HeightCm"]))
            with col3:
                st.metric("Life Span", row["LifeSpan"] if row["LifeSpan"] else "—")

            # Extra details block
            st.markdown("### Details")
            st.write(
                f"**Group:** {row['Group'] or '—'}  \n"
                f"**Origin:** {row['Origin'] or '—'}"
            )

        with img_tab:
            if row["ImageURL"]:
                st.image(
                    row["ImageURL"],
                    use_container_width=True,
                    caption=row["Name"],
                )
            else:
                st.info("No image available for this breed.")


# --------------------
# Feedback / suggestions
# --------------------
with st.expander(" Feedback / Suggestions"):
    st.write(
        "Help improve this dog knowledge base. "
        "We don't collect any cookies or information from you. "
        "Go crazy"
    )

    if "feedback_log" not in st.session_state:
        st.session_state.feedback_log = []

    user_msg = st.chat_input("Anything we should add or fix?")
    if user_msg:
        st.session_state.feedback_log.append(user_msg)
        st.toast("✅ Thanks! Your suggestion was recorded (locally).")

    if st.session_state.feedback_log:
        st.write("Your feedback this session:")
        for i, msg in enumerate(st.session_state.feedback_log, start=1):
            st.write(f"{i}. {msg}")
