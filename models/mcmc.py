import random
from matplotlib import pyplot as plt
import pymc as pm
import numpy as np
import pandas as pd
from scipy import stats
from statistics import mean, stdev
import arviz as az
import math

from models.interval import Interval

from typing import Tuple, List, Dict

def get_stats(result) -> Tuple[float, float]:
    return mean(result), stdev(result)

def confidence_interval(mean: float, sd: float, n: int):
    interval = stats.norm.interval(0.95, mean, sd/math.sqrt(n))
    return Interval(interval[0], interval[1])

def calc_difference(og, mean):
    return abs(og - mean)

DRAWS = 100
CHAIN_COUNT = 6

# Get the mean, stdev, and confidence interval of the distribution
def mcmc(result: List[float]) -> Tuple[float, float, Interval]:
    with pm.Model():
        pm.Normal('model', quiet=True, mu=mean(result), sigma=stdev(result))
        step = pm.Metropolis()
        # Sample with Markov chains
        trace = pm.sample(quiet=True, progressbar=False, draws=DRAWS, chains=CHAIN_COUNT, step=step, return_inferencedata=True)
    summary = az.summary(trace, round_to=10)

    model_mean = summary["mean"]["model"]
    model_stdev = summary["sd"]["model"]
    ci = confidence_interval(model_mean, model_stdev, 3)

    return model_mean, model_stdev, ci
