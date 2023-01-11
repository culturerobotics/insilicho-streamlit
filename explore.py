import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from insilicho import run
from exp_def import ranges, run_exp

pd.options.mode.chained_assignment = None  # default='warn'

st.set_page_config(layout="wide", page_title="Insilicho Explorer")

with st.sidebar:
    with st.expander(
        "Experiment Data",
        expanded=False,
    ):

        # Download button
        with open("example.csv") as f:
            st.download_button(
                "Download Example CSV",
                f,
                file_name="example.csv",
                mime="text/csv",
            )

        # File uploader
        user_data = st.file_uploader(
            "Data",
            type=["csv"],
            help="1. CSV file must be formatted as the example file with the same column names, Glc-> Glucose and Gln->Glutamine. To add error bars, column name ending in '_std' is needed.\n"
            "2. Data and Model source: Model uncertainty-based evaluation of process strategies during scale-up of biopharmaceutical processes, Moller et al., Computers and Chemical Engineering 134 (2020) 106693\n"
            "3. Culture Biosciences does not get a copy of your data. Your data may hit streamlit backend, please see https://discuss.streamlit.io/t/where-does-the-data-go-when-using-file-uploader-when-does-it-get-deleted/8269 for privacy concerns.",
        )

        # Unit conversion needed for conc of species
        convert_units = st.checkbox(
            "Convert metabolite units",
            value=False,
            help="Underlying simulation generates metabolites in mM units, while some sampling systems generate data in [g/L] units. Checking this box will convert [g/L] for metabolites into [mM].",
        )

    with st.expander("Simulation", expanded=True):
        Ndays = st.slider("Ndays (days)", 1, 15, 10)
        Nsamples = st.slider("NSamples (per day)", 1, 12, 4)

    with st.expander("Initial conditions", expanded=True):
        V = st.slider(
            "V (mL)", 10.0, 150.0, 20.0, help="Starting volume in the reactor"
        )
        Xv = st.slider(
            "Xv (Mcells/mL)",
            min_value=0.01,
            max_value=10.0,
            value=0.25,
            help="Starting cell concentration",
        )

    with st.expander("Control", expanded=False):
        sliders = {}
        ranged_params = ranges(Ndays)
        for key, vals in ranged_params.items():
            if vals[1] < 0.01:
                step = 1e-4
            else:
                step = 0.01
            try:
                help_text = vals[4]
            except IndexError:
                help_text = ""
            sliders[key] = st.slider(
                key + "(" + vals[3] + ")",
                min_value=float(vals[0]),
                max_value=float(vals[1]),
                value=float(vals[2]),
                step=step,
                format="%f",
                help=help_text,
            )

    with st.expander("Model params", expanded=False):
        mu_max = st.slider("mu_max (1/hr)", 0.0, 0.2, 0.043, help="Cell growth rate")
        mu_d_max = st.slider(
            "mu_d_max (1/hr)", 0.01, 1.0, 0.06, help="Max cell death rate"
        )
        mu_d_min = st.slider(
            "mu_d_min (1/hr)",
            0e1,
            1e-1,
            1e-3,
            step=1e-4,
            format="%f",
            help="Min cell death rate",
        )
        st.markdown("""---""")
        q_mab = st.slider(
            "q_mab (pico-gram/cell/hr)",
            0.01,
            1.0,
            0.312,
            help="q-rate for mAb production, per cell basis",
        )
        q_lac_max = st.slider(
            "q_lac_max (pico-mol/cell/hr)",
            0.0,
            5.0,
            0.2,
            help="q-rate for lactate uptake when glucose falls below 0.5mmol",
        )
        st.markdown("""---""")
        Ki_amm = st.slider(
            "Ki_amm (mmol/L)",
            0.0,
            100.0,
            10.0,
            help="Inhibitory concentration of ammonia, causes mAb suppression",
        )
        st.markdown("""---""")
        Y_amm_gln = st.slider(
            "Y_amm_gln",
            0.0,
            20.0,
            0.9,
            help="stoichiometric yield coefficient b/w ammonia production and glutamine consumption",
        )
        Y_lac_glc = st.slider(
            "Y_lac_glc",
            0.0,
            20.0,
            0.25,
            help="stoichiometric yield coefficient b/w lactate production and glucose consumption",
        )

with st.expander("What does this app do?", expanded=True):
    st.write("##### Simulates a Chinese Hamster Ovary (CHO) growth run in the cloud")
    st.write(
        "- Choose different parameters (model, control, feeding, initial conditions) from the sidebar to simulate a CHO growth experiment in a cloud bioreactor\n"
        "- App currently supports constant feeding profiles only (stay tuned for updates!)\n"
        "- Optionally, upload sampling data to see how your experiments line up to the model\n"
        "- App source code at [this repo](https://github.com/culturerobotics/insilicho-streamlit#readme)\n"
        "- Underlying model source code (Insilicho) and references [here](https://github.com/culturerobotics/insilicho#readme)\n"
    )

# -----------------------------------#
# Convert feed into correct units
for k, v in sliders.items():
    ks = k.split("_")
    if ks[0] == "day" and ks[-1] == "feed":
        sliders[k] = v / 1000 / 24.0  # convert day_i_feed from mL/day to L/h

# Setup params.
config = {
    "parameters": {
        "mu_max": mu_max,
        "mu_d_max": mu_d_max,
        "mu_d_min": mu_d_min,
        "q_mab": q_mab * 1e-9,  # pico to mg
        "q_lac_max": q_lac_max * 1e-9,
        "Y_amm_gln": Y_amm_gln,
        "Y_lac_glc": Y_lac_glc,
        "Ki_amm": Ki_amm,
        "Cglc_feed": sliders["feed_glc"],
        "Cgln_feed": sliders["feed_gln"],
        "Ndays": Ndays,
        "Nsamples": Nsamples,
    },
}

# Instantiate model.
model_instance = run.GrowCHO(
    config,
    feed_fn=None,
    temp_fn=None,
    param_rel_stddev=0,
)

# Run model with these settings.
sampling_data, score = run_exp(
    sliders,
    model=model_instance,
    Xv=Xv * 1e9,
    V=V * 1e-3,
)
keys = list(sampling_data.keys())

# Extract data.
sampling_df = pd.DataFrame.from_dict(sampling_data)

# Print titer
st.text(f"Final Titer [mg/L]: {score:0.1f}")


with st.expander("Model results", expanded=True):
    user_data = user_data or "example.csv"
    user_df = pd.read_csv(user_data)

    def altair_plot(
        insilicho_name,
        csv_header_name,
        conversion_factor=1.0,
        title="mM",
        tmax=Ndays * 24,
        color="orange",
    ):
        stddev_name = csv_header_name + "_std"

        if not convert_units:
            conversion_factor = 1.0

        # simulated trace
        sim = (
            alt.Chart(sampling_df)
            .mark_line(strokeWidth=4, color=color)
            .encode(
                x=alt.X("time", title="Time [hrs]", scale=alt.Scale(domain=[0, tmax])),
                y=alt.Y(insilicho_name, title=title),
            )
        )
        included_plots = [sim]

        if user_data:
            df_loc = user_df
            try:
                df_loc = user_df[user_df.time < tmax]
            except (KeyError, AttributeError):
                df_loc = user_df
                df_loc["time"] = user_df.iloc[:, 0]

            # Try reading mean data
            try:
                df_loc["mean"] = conversion_factor * df_loc[csv_header_name]
            except (KeyError, AttributeError):
                df_loc["mean"] = np.NaN

            # Try reading stddev
            try:
                df_loc["std"] = conversion_factor * df_loc[stddev_name]
            except (KeyError, AttributeError):
                df_loc["std"] = 0 * df_loc["mean"]

            # drop all irrelevant data
            df = df_loc[["mean", "std", "time"]]

            # the base chart
            base = alt.Chart(df).transform_calculate(
                ymin="datum.mean-1*datum.std", ymax="datum.mean+1*datum.std"
            )
            # generate the error bars
            errorbars = base.mark_errorbar(color="blue", extent="ci").encode(
                x="time",
                y="ymin:Q",
                y2="ymax:Q",
            )
            # generate the points
            points = base.mark_point(filled=True, size=50, color="red").encode(
                x=alt.X("time", scale=alt.Scale(domain=(0, tmax))),
                y=alt.Y("mean", scale=alt.Scale(zero=False)),
            )
            included_plots.extend([errorbars, points])

        st.altair_chart(
            alt.LayerChart(layer=tuple(included_plots)),
            use_container_width=True,
        )

    altair_plot("Xv", "Xv", 1, "Xv [MCells/L]", color="green")
    altair_plot("Cglc", "C_Glc", 1000 / 180, "Glucose [mM]", color="orange")
    altair_plot("Cgln", "C_Gln", 1000 / 146.15, "Glutamine [mM]", color="orange")
    altair_plot(
        "Camm", "C_Amm", 1000 / 18.04, "Amm [mM]", color="purple"
    )  # ammonia or ammonium?
    altair_plot(
        "Clac", "C_Lac", 1000 / 90.08, "Lac [mM]", color="purple"
    )  # Lactate or lactic acid?
    altair_plot(
        "Cmab", "C_mab", 1, "mAbs [mg/L]", color="blue"
    )  # TODO: conversion factor for mabs
    # altair_plot("Osmolarity", "Osmolarity", 1, "Osmolarity [mOsm/kg]", color="blue")

# Show all data.
with st.expander("Sampled Data", expanded=False):
    st.write(sampling_df)

# Show params.
with st.expander("Control Params", expanded=False):
    st.write(sliders)

# Show control.
with st.expander("Applied controls", expanded=False):
    # Unpack.
    fr = model_instance._full_result
    tdata = list(fr.t)
    (Xv, Xt, Cglc, Cgln, Clac, Camm, Cmab, Coxygen, V, pH) = fr.state.transpose()
    F = fr.state_vars[:, 0]
    T = fr.state_vars[:, 1]
    Osmolarity = fr.state_vars[:, 9]
    df_Temp = pd.DataFrame.from_dict({"T (degC)": T, "t (hrs)": tdata})
    df_F = pd.DataFrame.from_dict({"F (mL/day)": F * 24 * 1000, "t (hrs)": tdata})
    df_V = pd.DataFrame.from_dict({"V (mL)": V * 1000, "t (hrs)": tdata})
    st.write("Temperature:")
    st.line_chart(df_Temp, x="t (hrs)")
    st.markdown("""---""")
    st.write("Feed:")
    st.line_chart(df_F, x="t (hrs)")
    st.markdown("""---""")
    st.write("Volume:")
    st.line_chart(df_V, x="t (hrs)")
