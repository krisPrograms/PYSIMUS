from statistics import mean
from typing import List
from models.interval import Interval

import random

type Weights = List[List[float]]
type IWeights = List[List[Interval]]

# Converts a single probability value into a list of subintervals
# The union of the subintervals is [probability - uncertainty, probability + uncertainty], clamped to [0, 1]
def __generate_subintervals (probability: float, uncertainty: float, num_subintervals: int):
    subintervals: List[Interval] = []
    for i in range(num_subintervals):
        offset = (2 * i - num_subintervals + 1) / num_subintervals * uncertainty
        distance = uncertainty / num_subintervals
        low: float  = probability + offset - distance
        high: float = probability + offset + distance
        subinterval = Interval(low, high, close_left=(i>0)).clamp(0, 1)
        subintervals.append(subinterval)
    return subintervals

# Converts a single probability value into a list of subintervals
# The union of the subintervals is [probability - uncertainty, probability + uncertainty], clamped to [0, inf)
def __generate_subintervals_ctmc (probability: float, uncertainty: float, num_subintervals: int):
    subintervals: List[Interval] = []
    for i in range(num_subintervals):
        offset = (2 * i - num_subintervals + 1) / num_subintervals * uncertainty
        distance = uncertainty / num_subintervals
        low: float  = probability + offset - distance
        high: float = probability + offset + distance
        subinterval = Interval(low, high, close_left=(i>0)).floor(0)
        subintervals.append(subinterval)
    return subintervals


# Checks to see if it's possible to generate a combination of subintervals such that their sum contains 1
# This is not very fast (exponential time), but there usually won't be many subintervals
# If you as a future maintainer want to optimize this, you could look into linear programming
def __can_generate_valid_transition (transition: List[List[Interval]], current_combination: List[Interval]=[]) -> bool:
    prob_index = len(current_combination)
    if prob_index >= len(transition):
        sum_interval = Interval(0.0, 0.0)
        for subinterval in current_combination:
            sum_interval += subinterval
        if sum_interval.contains(1.0):
            return True
        else:
            return False

    for subinterval in transition[prob_index]:
        interval_selection = [p for p in current_combination]
        interval_selection.append(subinterval)
        if __can_generate_valid_transition(transition, current_combination=interval_selection):
            return True
    return False


def __pick_subtransitions (subinterval_lists: List[List[Interval]]) -> List[List[Interval]]:
    num_probabilities = len(subinterval_lists)
    num_subintervals = len(subinterval_lists[0])
    transitions: List[List[Interval]] = []
    while True:
        transitions = []
        remaining_subinterval_lists = [[subinterval for subinterval in subintervals] 
                                                    for subintervals in subinterval_lists]
        restart = False

        for remaining_subinterval_count in range(num_subintervals, 0, -1):
            # If we can't generate a valid pairing of intervals, just start over
            restart = True
            if not __can_generate_valid_transition(subinterval_lists):
                restart = True
                break
            for _ in range(100):
                selections = [random.randint(0, remaining_subinterval_count-1) for _ in range(num_probabilities)]
                selected_subintervals = [remaining_subinterval_lists[i][selections[i]] for i in range(num_probabilities)]
                # Check if we can pick 1 from our chosen intervals
                sum_interval = Interval(0, 0)
                for subinterval in selected_subintervals:
                    sum_interval = sum_interval + subinterval
                if not sum_interval.contains(1.0):
                    continue
                transitions.append(selected_subintervals)
                for i in range(num_probabilities):
                    remaining_subinterval_lists[i].pop(selections[i])
                restart = False
                break
        if not restart: return transitions

def __pick_subtransitions_ctmc (subinterval_lists: List[List[Interval]]) -> List[List[Interval]]:
    num_probabilities = len(subinterval_lists)
    num_subintervals = len(subinterval_lists[0])
    transitions: List[List[Interval]] = []
    
    # Since CTMC doesn't require subintervals to sum to 1, this is way simpler
    remaining_subinterval_lists = [[subinterval for subinterval in subintervals] 
                                                for subintervals in subinterval_lists]
    for remaining_subinterval_count in range(num_subintervals, 0, -1):
        selections = [random.randint(0, remaining_subinterval_count-1) for _ in range(num_probabilities)]
        selected_subintervals = [remaining_subinterval_lists[i][selections[i]] for i in range(num_probabilities)]
        transitions.append(selected_subintervals)
        for i in range(num_probabilities):
            remaining_subinterval_lists[i].pop(selections[i])
    return transitions


def generate_uncertain_submodels (model: Weights,
                       uncertainty: float=0.01,
                       num_subintervals: int=3) -> List[IWeights]:
    subtransition_lists: List[List[List[Interval]]] = []
    for transition in model:
        # For cases where there is only one weight, don't mess with the probabilities
        # If we create subintervals that don't have 1, the program ends up breaking
        if len(transition) == 1:
            subinterval_lists = [[Interval(prob, prob) for _ in range(num_subintervals)] for prob in transition]
        else:
            subinterval_lists = [__generate_subintervals(prob, uncertainty, num_subintervals) for prob in transition]
        subtransitions = __pick_subtransitions(subinterval_lists)
        subtransition_lists.append(subtransitions)
    # Transpose the lists of subintervals into submodels
    submodels: List[IWeights] = [list(transition_selection) for transition_selection in zip(*subtransition_lists)]
    return submodels

def generate_uncertain_submodels_ctmc (model: Weights,
                       uncertainty: float=0.01,
                       num_subintervals: int=3) -> List[IWeights]:
    subtransition_lists: List[List[List[Interval]]] = []
    for transition in model:
        subinterval_lists = [__generate_subintervals_ctmc(prob, uncertainty, num_subintervals) for prob in transition]
        subtransitions = __pick_subtransitions_ctmc(subinterval_lists)
        subtransition_lists.append(subtransitions)
    # Transpose the lists of subintervals into submodels
    submodels: List[IWeights] = [list(transition_selection) for transition_selection in zip(*subtransition_lists)]
    return submodels


def skew_uncertain_model (submodel: IWeights, max_offset: float=0.005) -> IWeights:
    delta_interval = Interval(-max_offset, max_offset)
    skewed_submodel: IWeights = []
    for transition in submodel:
        # For cases where there is only one transition (the weight is just 1)
        # we should not actually add any skew
        if len(transition) == 1:
            skewed_submodel.append(transition)
            continue
        while True:
            skewed_transition: List[Interval] = []
            for interval in transition:
                skewed_transition.append(interval + delta_interval.get_random())
            # Rearranging here is to match types
            if __can_generate_valid_transition([[interval] for interval in skewed_transition]):
                skewed_submodel.append(skewed_transition)
                break
    return skewed_submodel

def skew_uncertain_model_ctmc (submodel: IWeights, max_offset: float=0.005) -> IWeights:
    delta_interval = Interval(-max_offset, max_offset)
    skewed_submodel: IWeights = []
    for transition in submodel:
        skewed_transition: List[Interval] = []
        for interval in transition:
            skewed_transition.append(interval + delta_interval.get_random())
        skewed_submodel.append(skewed_transition)    
    return skewed_submodel


def decide_submodel (submodel: IWeights, precision: int=-1) -> Weights:
    model: Weights = []
    for transition in submodel:
        # Probabilities need to sum to 1; loop until that's the case
        # We know that each transition CAN sum to 1, as we made sure
        # of that before; we just need to generate until we get it
        # It would probably help to prune away any values that cannot be attained
        new_transition: List[float] = [0.0]
        while sum(new_transition) != 1.0:
            new_transition: List[float] = [interval.get_random(precision=precision) for interval in transition]
        model.append(new_transition)
    return model

def decide_submodel_ctmc (submodel: IWeights, precision: int=-1) -> Weights:
    model: Weights = []
    for transition in submodel:
        # Unlike with DTMC/DTMDP, weights need not sum to 1
        new_transition: List[float] = [interval.get_random(precision=precision) for interval in transition]
        model.append(new_transition)
    return model


# This only performs a linear average
def average_models (models: List[Weights]) -> Weights:
    resultant_model: Weights = []
    # This zip mess is to turn models, containing transitions, containing weights
    # into transitions, containing weights, containing models
    for transition in list(zip(*models)):
        resultant_transition: List[float] = []
        for weight in list(zip(*transition)):
            # Linear average
            resultant_weight: float = mean(weight)
            resultant_transition.append(resultant_weight)
        resultant_model.append(resultant_transition)
    return resultant_model
                
