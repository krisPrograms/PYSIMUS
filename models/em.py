from statistics import mean
from statistics import stdev
import numpy as np
from models.interval import Interval
import pandas as pd
import seaborn as sns
from sklearn.mixture import GaussianMixture
from scipy import stats
import matplotlib.pyplot as plt
import math
import random

from typing import Tuple, List

# https://en.wikipedia.org/wiki/Expectation%E2%80%93maximization_algorithm

# return distribution stats
def get_stats(result) -> Tuple[float, float]:
    return mean(result), stdev(result)

# calculate confidence interval from EM results
def confidence_interval(mean: float, sd: float, n: int) -> Tuple[float, float]:
    return stats.norm.interval(0.95, mean, sd / math.sqrt(n))

# calculates the difference between each EM distribution mean and the original model result
def calc_difference(og, means):
    differences = []

    for i in range(0, len(means)):
        diff = abs(og-means[i])[0]
        differences.append(diff)

    return differences

# construct gaussian mixture using the EM algorithm and plot the distribution
def EM(values,num,n) -> Tuple[float, float, float]:
    gmm = GaussianMixture(tol=0.000001)
    gmm.fit(np.expand_dims(values, 1))
    for mu, sd, p in zip(gmm.means_.flatten(), np.sqrt(gmm.covariances_.flatten()), gmm.weights_):
        sns.distplot(values, bins=7, kde=False, norm_hist=True, label="{} Intervals Results".format(n))
        return mu, sd, p
    return 0, 0, 0

# calculates the smallest confidence interval, i.e. the most precise result
def interval_difference(intervals: List[Tuple[float, float]]) -> Tuple[int, float]:
    print(intervals)
    minimum = intervals[0][1] - intervals[0][0]
    min_index = 0

    for i in range(1,len(intervals)):
        cur_diff = intervals[i][1] - intervals[i][0]
        if cur_diff < minimum:
            minimum = cur_diff
            min_index = i + 1

    return min_index, minimum


def main(query_index, line_colors):
    ##########################################################################
    # get the needed data

    num_intervals = ["3", "5", "7"]
    num = 0
    cur_distribution = 1

    og_result = original[query_index]
    result_3 = three_intervals[query_index]
    result_5 = five_intervals[query_index]
    result_7 = seven_intervals[query_index]

    results = [result_3, result_5, result_7]
    all_data = []
    means: List[float] = []
    intervals: List[Interval] = []

    ##########################################################################
    # perform the EM algorithm and plot results

    for result in results:
        mean, stddev = get_stats(result)
        print(f"Input Gaussian {num_intervals[num]}: μ = {mean}, σ = {round(stddev, 2)}")
        values = result.array
        all_data.extend(values)
        em = EM(values,cur_distribution,num_intervals[num],line_colors)
        cur_interval = confidence_interval(em[0],em[1],int(num_intervals[num]))
        intervals.append(cur_interval)
        means.append(em[0])
        num = num+1
        cur_distribution = cur_distribution + 1

    x = np.linspace(min(all_data), max(all_data))
    plt.legend()

    # determine smallest confidence interval, and either plot or table
    print("Smallest Confidence Interval: ", interval_difference(intervals))
    # calc the difference between EM results and og result, either plot or table
    calc_difference(og_result.array, means)

# read data
query_results = pd.read_csv("DTMC_GAL_Results_Size2.csv")
original = query_results[query_results["Model #"] == "OG"].copy()
three_intervals = query_results[1:4]
five_intervals = query_results[4:9]
seven_intervals = query_results[9:16]

random.seed(100)
line_colors = ["blue", "chocolate", "green"]

# enter desired query
main("Query 3 Result ", line_colors)
