import json
import operator
from pathlib import Path

import pandas as pd
import streamlit as st


# =====================================================
# SHAFIQ ALPHA - UNIVERSAL CUSTOM FILTER ENGINE
# API INDEPENDENT FILTER SYSTEM
# =====================================================

FILTER_FILE = Path(__file__).parent / "saved_filters.json"

OPERATORS = {
    "Greater than (>)": operator.gt,
    "Greater than or equal (>=)": operator.ge,
    "Less than (<)": operator.lt,
    "Less than or equal (<=)": operator.le,
    "Equal to (=)": operator.eq,
    "Not equal to (!=)": operator.ne,
}


def load_saved_filters():
    if not FILTER_FILE.exists():
        return {}

    try:
        with open(FILTER_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_filters(filters):
    with open(FILTER_FILE, "w", encoding="utf-8") as file:
        json.dump(filters, file, indent=4, ensure_ascii=False)


def apply_filters(data, rules):
    if data is None or data.empty:
        return pd.DataFrame()

    result = data.copy()

    for rule in rules:
        column = rule.get("column")
        condition = rule.get("operator")
        value = rule.get("value")

        if column not in result.columns:
            continue

        if condition in OPERATORS:
            series = pd.to_numeric(result[column], errors="coerce")
            try:
                target = float(value)
                result = result[OPERATORS[condition](series, target)]
            except (ValueError, TypeError):
                continue

        elif condition == "Contains":
            result = result[
                result[column].astype(str).str.contains(
                    str(value), case=False, na=False
                )
            ]

        elif condition == "Does not contain":
            result = result[
                ~result[column].astype(str).str.contains(
                    str(value), case=False, na=False
                )
            ]

        elif condition == "Is empty":
            result = result[
                result[column].isna()
                | (result[column].astype(str).str.strip() == "")
            ]

        elif condition == "Is not empty":
            result = result[
                result[column].notna()
                & (result[column].astype(str).str.strip() != "")
            ]

    return result


def custom_filter_builder(data, key="main"):
    st.markdown("## 🔎 Custom Filter Builder")

    if data is None or data.empty:
        st.warning("No stock data available.")
        return pd.DataFrame()

    saved = load_saved_filters()

    st.markdown("### Saved Filters")

    saved_names = list(saved.keys())

    selected = st.selectbox(
        "Load a saved filter",
        ["None"] + saved_names,
        key=f"load_{key}"
    )

    if selected != "None":
        rules = saved[selected]
    else:
        rules = []

    st.markdown("### Create Filter")

    columns = list(data.columns)

    selected_column = st.selectbox(
        "Select data column",
        columns,
        key=f"column_{key}"
    )

    condition_options = list(OPERATORS.keys()) + [
        "Contains",
        "Does not contain",
        "Is empty",
        "Is not empty"
    ]

    condition = st.selectbox(
        "Select condition",
        condition_options,
        key=f"condition_{key}"
    )

    value = ""

    if condition not in ["Is empty", "Is not empty"]:
        value = st.text_input(
            "Enter filter value",
            key=f"value_{key}"
        )

    if st.button("➕ Add Filter", key=f"add_{key}"):
        rules.append({
            "column": selected_column,
            "operator": condition,
            "value": value
        })

    st.markdown("### Active Conditions")

    if rules:
        for index, rule in enumerate(rules):
            st.write(
                f"{index + 1}. {rule['column']} "
                f"{rule['operator']} {rule['value']}"
            )

        if st.button("🗑 Clear All Filters", key=f"clear_{key}"):
            rules = []

    filtered_data = apply_filters(data, rules)

    st.markdown("### Save Filter")

    filter_name = st.text_input(
        "Enter a name for this filter",
        key=f"name_{key}"
    )

    if st.button("💾 Save Filter", key=f"save_{key}"):
        if filter_name.strip():
            saved[filter_name.strip()] = rules
            save_filters(saved)
            st.success("Filter saved successfully.")
        else:
            st.warning("Please enter a filter name.")

    st.markdown("### Filter Results")

    st.success(
        f"{len(filtered_data)} stocks found out of {len(data)}"
    )

    st.dataframe(
        filtered_data,
        use_container_width=True,
        hide_index=True
    )

    return filtered_data
