import dataclasses

import numpy as np
from barebones import growth_model, parameters
from scipy.integrate import odeint


def solve(
    params: parameters.InputParameters,
    initial_conditions: parameters.InitialConditions,
    model=growth_model.model,
    tspan=np.linspace(0, 288, 10000),
    feed_fn=None,
    temp_fn=None,
    solver_hmax=np.inf,
):
    IC = [
        initial_conditions.Xv,
        initial_conditions.Xt,
        initial_conditions.Cglc,
        initial_conditions.Cgln,
        initial_conditions.Clac,
        initial_conditions.Camm,
        initial_conditions.Cmab,
        initial_conditions.Coxygen,
        initial_conditions.V,
        initial_conditions.pH,
    ]

    args = []
    for field in dataclasses.fields(params):
        args.append(getattr(params, field.name))

    state_model, info = odeint(
        model,
        IC,
        tspan,
        (
            args,
            feed_fn,
            temp_fn,
        ),
        tfirst=True,
        printmessg=False,
        full_output=True,
        hmax=solver_hmax,
    )
    state_vars = []
    for i in range(len(tspan)):
        state_vars.append(
            list(
                growth_model.state_vars(
                    tspan[i], state_model[i], params, feed_fn, temp_fn
                )
            )
        )
    state_vars = np.array(state_vars, dtype=float)
    return state_model, state_vars, info