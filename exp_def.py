import sys

sys.path.append("barebones")
from barebones import run

initial_config = {
    "parameters": {
        "Ndays": 12,
        "Nsamples": 2,
        "mu_max": 0.043,  # "1/hr",
        "mu_d_max": 0.06,  # "1/hr",
        "mu_d_min": 0.001,  # "1/hr",
        "k_glc": 0.2,  # "mmol/L",
        "k_gln": 2.5,  # "mmol/L",
        "K_lys": 0.001,  # "1/hr",
        "Ks_amm": 10.0,  # "mmol/L",
        "Ki_amm": 10.0,  # "mmol/L",
        "Ks_glc": 0.02,  # "mmol/L",
        "Ks_gln": 0.03,  # "mmol/L",
        "q_mab": 3.12e-10,  # "mmol/L/hr",
        "q_glc_max": 0.05e-9,  # "mmol/L/hr",
        "q_gln_max": 0.054e-9,  # "mmol/L/hr",
        "q_lac_max": 0.2e-9,  # "mmol/L/hr",
        "Y_amm_gln": 0.90,
        "Y_lac_glc": 0.25,
    }
}  # From SI, Table 2 of "Model uncertainty-based evaluation of process strategies during scale-up of biopharmaceutical process"

RealCHO = run.GrowCHO(initial_config, None, None)

# Score is final mAbs concentration
def score(exp_res):
    return exp_res["Cmab"][-1]


def run_exp(
    factor_settings, model=RealCHO, Xv=8e6, V=0.02, plot=False, sampling_stddev=0.05
):
    """Run an experiment with the supplied factor settings (falling back to defaults for missing settings)."""

    default_settings = {
        "batch_glc": 50,
        "batch_gln": 10,
        "batch_pH": 7.0,
        "feed_glc": 50,
        "feed_gln": 1,
        "prod_start_eft": 48,
        "batch_temp": 36,
        "prod_temp": 36,
        "day_0_feed": 0,
        "day_1_feed": 0,
        "day_2_feed": 0,
        "day_3_feed": 0,
        "day_4_feed": 0,
        "day_5_feed": 0,
        "day_6_feed": 0,
        "day_7_feed": 0,
        "day_8_feed": 0,
        "day_9_feed": 0,
    }

    settings = default_settings | factor_settings

    def feed(t):
        feed_array = [
            settings["day_0_feed"],
            settings["day_1_feed"],
            settings["day_2_feed"],
            settings["day_3_feed"],
            settings["day_4_feed"],
            settings["day_5_feed"],
            settings["day_6_feed"],
            settings["day_7_feed"],
            settings["day_8_feed"],
            settings["day_9_feed"],
        ]
        # Repeat last entry to avoid index out of bounds.
        feed_array += 100 * [settings["day_9_feed"]]
        return feed_array[int(t // 24)]

    def temp(t):
        if t < settings["prod_start_eft"]:
            return settings["batch_temp"]
        else:
            return settings["prod_temp"]

    model.params.Cglc_feed = settings["feed_glc"]
    model.params.Cgln_feed = settings["feed_gln"]

    model.feed_fn = feed
    model.temp_fn = temp

    res = model.execute(
        {
            "Cglc": settings["batch_glc"],
            "Cgln": settings["batch_gln"],
            "pH": settings["batch_pH"],
            "V": V,
            "Xv": Xv,
        },
        plot=plot,
        sampling_stddev=sampling_stddev,
    )

    return res, score(res)


ranges = {
    "batch_glc": (0, 300, 45, "mM", "starting glucose conc. in batch media"),
    "batch_gln": (0, 50, 5.7, "mM", "starting glutamine conc. in batch media"),
    "batch_pH": (6.7, 7.4, 6.90, "-", "controlled pH value"),
    "feed_glc": (50, 300, 140, "mM", "glucose conc. in feed"),
    "feed_gln": (0, 50, 5, "mM", "glutamine conc. in feed"),
    "prod_start_eft": (
        24,
        24*10,
        72,
        "hrs",
        "time marking shift from batch to production",
    ),
    "batch_temp": (33, 40, 37, "degC", "T of batch phase"),
    "prod_temp": (33, 40, 37, "degC", "T of production phase"),
    "day_0_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_1_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_2_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_3_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_4_feed": (0, 50.0, 1.750, "mL/day", "feed in mL/day"),
    "day_5_feed": (0, 50.0, 1.750, "mL/day", "feed in mL/day"),
    "day_6_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_7_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_8_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
    "day_9_feed": (0, 50.0, 0.0, "mL/day", "feed in mL/day"),
}
