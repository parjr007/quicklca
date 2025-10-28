import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

st.set_page_config(page_title="Quick LCA Dashboard", layout="wide")
st.title("Quick LCA Tool")

impact_categories = [
    "GWP100", "Acidification", "Eutrophication", "Photochemical Ozone", "Water Use",
    "Ecotoxicity", "Human Toxicity", "Resource Depletion (Fossil)", "Resource Depletion (Minerals)",
    "Fine Particulate", "Ozone Depletion", "Land Use", "Freshwater Depletion"
]

category_units = {
    "GWP100": "kg CO2 eq.",
    "Acidification": "kg SO2 eq.",
    "Eutrophication": "kg PO4 eq.",
    "Photochemical Ozone": "kg C2H4 eq.",
    "Water Use": "m³",
    "Ecotoxicity": "CTUe",
    "Human Toxicity": "CTUh",
    "Resource Depletion (Fossil)": "MJ",
    "Resource Depletion (Minerals)": "kg Sb eq.",
    "Fine Particulate": "kg PM2.5 eq.",
    "Ozone Depletion": "kg CFC11 eq.",
    "Land Use": "m²a",
    "Freshwater Depletion": "m³"
}

st.sidebar.subheader("Dashboard Options")
impact_choice = st.sidebar.selectbox("Select LCA Impact Category", impact_categories)
chosen_unit = category_units[impact_choice]
st.write(f"**Selected Impact Category:** {impact_choice} ({chosen_unit})")

st.markdown("""
#### Instructions
- Prepare Excel with columns: Material | Quantity | Unit | [13 emission categories]
- Only rows with Total Emission >0 are graphed
- **Blue columns/results are locked**
- Bar chart: Hotspots (>10%) in red; **percent value only on hover!**
""")

# File upload section
st.subheader("Upload Excel (.xlsx) with all categories")
file = st.file_uploader("Choose Excel file", type=['xlsx'])

if file:
    df_input = pd.read_excel(file)
    st.success("File loaded!")

    expected_cols = ['Material', 'Quantity', 'Unit'] + impact_categories
    missing = [col for col in expected_cols if col not in df_input.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
    else:
        # Editable input: only Quantity and Unit
        editable_cols = ['Material', 'Quantity', 'Unit']
        edited = st.data_editor(
            df_input[editable_cols],
            use_container_width=True,
            disabled=[True, False, False],
            num_rows="dynamic"
        )

        emission_factors = df_input[impact_choice]
        edited["Emission Factor"] = emission_factors

        # Formula and results
        edited["Total Emission"] = edited["Quantity"] * edited["Emission Factor"]
        total_emission = edited["Total Emission"].sum()
        edited["Percent Emission"] = np.round(100 * edited["Total Emission"] / total_emission, 2) if total_emission > 0 else 0

        st.subheader(f"Results for {impact_choice} (Blue, Locked)")
        results = edited[["Material", "Total Emission", "Percent Emission"]]

        def pct_color(val):
            color = "red" if isinstance(val, float) and val > 10 else "#0074D9"
            return f"background-color: {color}; color: white;" if val > 10 else ""
        styled_results = results.style.applymap(pct_color, subset=["Percent Emission"])
        st.dataframe(styled_results, use_container_width=True)

        # --- Plotly Graph: clean, hover values only! ---
        nonzero = results[results["Total Emission"] > 0].reset_index(drop=True)

        # Abbreviate labels if long
        def abbreviate(name, maxlen=18):
            return name if len(str(name)) <= maxlen else str(name)[:maxlen] + "..."
        labels = [abbreviate(m) for m in nonzero["Material"]]
        percentages = nonzero["Percent Emission"]
        bar_colors = ["#FF4136" if v > 10 else "#0074D9" for v in percentages]

        st.subheader(f"{impact_choice} – Percent Emission by Material (Hover for Value)")
        if len(labels) > 0:
            fig = go.Figure([
                go.Bar(
                    x=labels,
                    y=percentages,
                    marker_color=bar_colors,
                    hovertemplate='<b>%{x}</b><br>Percent Emission: %{y:.2f}%<extra></extra>'
                )
            ])
            fig.update_layout(
                yaxis=dict(title="Percent Emission (%)", range=[0, max(percentages.max(), 20) + 5]),
                xaxis=dict(title="Material", tickangle=-45),
                title="Emission Hotspots (>10% in Red)",
                bargap=0.25,
                plot_bgcolor="white",
                height=400,
                width=max(800, len(labels)*50),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No nonzero emissions to display.")

        st.markdown(f"**Total Emission ({impact_choice}):** {total_emission:.2f} {chosen_unit}")
else:
    st.info("Please upload an Excel file with columns: Material, Quantity, Unit, and 13 emission factors.")

st.caption("Select the impact category and upload your input table. Graph and results update instantly. Hotspots are shown in red. Hover for value.")
