import json
import operator
from pathlib import Path

import pandas as pd
import streamlit as st


# =====================================================
# SHAFIQ ALPHA - UNIVERSAL FILTER ENGINE
# Founded & Developed by Magray Shafiq
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

TEXT_OPERATORS = [
    "Contains",
    "Does not contain",
    "Is empty",
    "Is not empty",
]

ALL_OPERATORS = list(OPERATORS.keys()) + TEXT_OPERATORS


# =====================================================
# FILTER STORAGE
# =====================================================

def load_saved_filters():
    try:
        if FILTER_FILE.exists():
            with open(FILTER_FILE, "r", encoding="utf-8") as f:
                result = json.load(f)
                return result if isinstance(result, dict) else {}
    except Exception:
        pass

    return {}


def save_filters(filters):
    try:
        with open(FILTER_FILE, "w", encoding="utf-8") as f:
            json.dump(filters, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Could not save filters: {e}")
        return False


# =====================================================
# CONDITION EVALUATION
# =====================================================

def evaluate_rule(data, rule):

    column = rule.get("column")
    condition = rule.get("operator")
    value = rule.get("value", "")

    if column not in data.columns:
        return pd.Series(False, index=data.index)

    series = data[column]

    if condition in OPERATORS:
        numeric_series = pd.to_numeric(series, errors="coerce")

        try:
            target = float(value)
            return OPERATORS[condition](numeric_series, target).fillna(False)
        except (ValueError, TypeError):
            return pd.Series(False, index=data.index)

    if condition == "Contains":
        return series.astype(str).str.contains(
            str(value), case=False, na=False, regex=False
        )

    if condition == "Does not contain":
        return ~series.astype(str).str.contains(
            str(value), case=False, na=False, regex=False
        )

    if condition == "Is empty":
        return series.isna() | (series.astype(str).str.strip() == "")

    if condition == "Is not empty":
        return series.notna() & (series.astype(str).str.strip() != "")

    return pd.Series(False, index=data.index)


def apply_filters(data, rules):

    if data is None or data.empty:
        return pd.DataFrame()

    if not rules:
        return data.copy()

    result_mask = None

    for index, rule in enumerate(rules):

        current_mask = evaluate_rule(data, rule)

        if index == 0:
            result_mask = current_mask
            continue

        logic = rule.get("logic", "AND")

        if logic == "OR":
            result_mask = result_mask | current_mask
        else:
            result_mask = result_mask & current_mask

    return data[result_mask.fillna(False)].copy()


# =====================================================
# MAIN FILTER BUILDER
# =====================================================

def custom_filter_builder(data, key="main"):

    st.markdown("## SHAFIQ ALPHA — CUSTOM SCREENER")

    if data is None or data.empty:
        st.warning("No stock data available.")
        return pd.DataFrame()

    saved = load_saved_filters()

    rules_key = f"filter_rules_{key}"
    loaded_key = f"loaded_filter_{key}"

    if rules_key not in st.session_state:
        st.session_state[rules_key] = []

    if loaded_key not in st.session_state:
        st.session_state[loaded_key] = None

    rules = st.session_state[rules_key]

    # -------------------------------------------------
    # SAVED FILTER MANAGEMENT
    # -------------------------------------------------

    st.markdown("### 1. Saved Filters")

    saved_names = list(saved.keys())

    selected = st.selectbox(
        "Select saved filter",
        ["None"] + saved_names,
        key=f"saved_select_{key}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Filter", key=f"load_btn_{key}"):

            if selected != "None":
                st.session_state[rules_key] = [
                    dict(rule) for rule in saved[selected]
                ]
                st.session_state[loaded_key] = selected
                st.rerun()
            else:
                st.warning("Select a saved filter first.")

    with col2:
        if st.button("Clear All", key=f"clear_btn_{key}"):
            st.session_state[rules_key] = []
            st.session_state[loaded_key] = None
            st.rerun()

    # -------------------------------------------------
    # ADD NEW CONDITION
    # -------------------------------------------------

    st.markdown("### 2. Add Conditions")

    columns = list(data.columns)

    with st.container(border=True):

        new_column = st.selectbox(
            "Select Field",
            columns,
            key=f"new_column_{key}"
        )

        new_operator = st.selectbox(
            "Select Condition",
            ALL_OPERATORS,
            key=f"new_operator_{key}"
        )

        new_value = ""

        if new_operator not in ["Is empty", "Is not empty"]:
            new_value = st.text_input(
                "Enter Value",
                key=f"new_value_{key}"
            )

        if st.button("➕ Add Condition", key=f"add_condition_{key}"):

            if new_operator not in ["Is empty", "Is not empty"] and not new_value.strip():
                st.warning("Please enter a value.")
            else:
                st.session_state[rules_key].append({
                    "column": new_column,
                    "operator": new_operator,
                    "value": new_value,
                    "logic": "AND"
                })
                st.rerun()

    # -------------------------------------------------
    # EDIT AND REMOVE CONDITIONS
    # -------------------------------------------------

    st.markdown("### 3. Active Conditions")

    rules = st.session_state[rules_key]

    if not rules:
        st.info("No conditions added yet.")

    for index, rule in enumerate(rules):

        with st.container(border=True):

            st.markdown(f"**Condition {index + 1}**")

            if index > 0:
                rule["logic"] = st.selectbox(
                    "Combine with previous condition",
                    ["AND", "OR"],
                    index=0 if rule.get("logic", "AND") == "AND" else 1,
                    key=f"logic_{key}_{index}"
                )

            rule["column"] = st.selectbox(
                "Field",
                columns,
                index=(
                    columns.index(rule["column"])
                    if rule.get("column") in columns else 0
                ),
                key=f"edit_column_{key}_{index}"
            )

            rule["operator"] = st.selectbox(
                "Condition",
                ALL_OPERATORS,
                index=(
                    ALL_OPERATORS.index(rule["operator"])
                    if rule.get("operator") in ALL_OPERATORS else 0
                ),
                key=f"edit_operator_{key}_{index}"
            )

            if rule["operator"] not in ["Is empty", "Is not empty"]:
                rule["value"] = st.text_input(
                    "Value",
                    value=str(rule.get("value", "")),
                    key=f"edit_value_{key}_{index}"
                )
            else:
                rule["value"] = ""

            if st.button(
                "🗑 Remove Condition",
                key=f"remove_{key}_{index}"
            ):
                st.session_state[rules_key].pop(index)
                st.rerun()

    # -------------------------------------------------
    # FILTER RESULTS
    # -------------------------------------------------

    st.markdown("### 4. Screener Results")

    filtered_data = apply_filters(
        data,
        st.session_state[rules_key]
    )

    st.success(
        f"{len(filtered_data)} stocks found out of {len(data)}"
    )

    st.dataframe(
        filtered_data,
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------------------------
    # SAVE / UPDATE / DUPLICATE / DELETE
    # -------------------------------------------------

    st.markdown("### 5. Manage Filters")

    filter_name = st.text_input(
        "Filter Name",
        value=st.session_state[loaded_key] or "",
        key=f"filter_name_{key}"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button("💾 Save New Filter", key=f"save_new_{key}"):

            name = filter_name.strip()

            if not name:
                st.warning("Enter a filter name.")
            elif not st.session_state[rules_key]:
                st.warning("Add at least one condition.")
            elif name in saved:
                st.warning("This name already exists. Use another name.")
            else:
                saved[name] = [
                    dict(rule) for rule in st.session_state[rules_key]
                ]

                if save_filters(saved):
                    st.session_state[loaded_key] = name
                    st.success("Filter saved.")
                    st.rerun()

    with col2:

        if st.button("✏️ Update Loaded Filter", key=f"update_{key}"):

            old_name = st.session_state[loaded_key]

            if not old_name or old_name not in saved:
                st.warning("Load a saved filter first.")
            elif not st.session_state[rules_key]:
                st.warning("Add at least one condition.")
            else:
                new_name = filter_name.strip() or old_name

                if new_name != old_name and new_name in saved:
                    st.warning("This filter name already exists.")
                else:
                    saved.pop(old_name)

                    saved[new_name] = [
                        dict(rule) for rule in st.session_state[rules_key]
                    ]

                    if save_filters(saved):
                        st.session_state[loaded_key] = new_name
                        st.success("Filter updated.")
                        st.rerun()

    col3, col4 = st.columns(2)

    with col3:

        if st.button("📋 Duplicate Filter", key=f"duplicate_{key}"):

            old_name = st.session_state[loaded_key]

            if not old_name or old_name not in saved:
                st.warning("Load a saved filter first.")
            else:
                copy_name = f"{old_name} Copy"

                counter = 2
                while copy_name in saved:
                    copy_name = f"{old_name} Copy {counter}"
                    counter += 1

                saved[copy_name] = [
                    dict(rule) for rule in st.session_state[rules_key]
                ]

                if save_filters(saved):
                    st.success(f"Duplicated as {copy_name}")
                    st.rerun()

    with col4:

        if st.button("❌ Delete Loaded Filter", key=f"delete_{key}"):

            old_name = st.session_state[loaded_key]

            if not old_name or old_name not in saved:
                st.warning("Load a saved filter first.")
            else:
                saved.pop(old_name)

                if save_filters(saved):
                    st.session_state[rules_key] = []
                    st.session_state[loaded_key] = None
                    st.success("Filter deleted.")
                    st.rerun()

    return filtered_data
