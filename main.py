import sys
from typing import List, Tuple
import os
import argparse

import prism
from lexer import Token, TokenType, lex
from models import *
from models.mcmc import mcmc

import pandas as pd

# CONSTANTS

"""
If you would like, this controls rounding precision for where it is needed.
WARNING: Raising this will dramatically increase runtime in some scenarios!
The runtime of the program scales linearly with the number of averagings
and the size of the model itself, and if using DTMC/MDP, scales superlinearly
with uncertainty, the number of submodels, and this rounding precision constant.
Any values above 5 will likely result in unusably high runtimes.
Stick to 3 unless you really need the precision.
"""
ROUNDING_PRECISION = 3

"""
These files temporarily store models and results. They are deleted afterwards,
so they are redefinable in case you for some reason have these files already.
"""
MODEL_TEMPFILE_NAME = ".tmp_samplemodelfile.txt"
RESULT_TEMPFILE_NAME = ".tmp_resultfile.txt"

##########################################################################################


# Extract the transition weights of a Prism model file for DTMC/MDP
def read_model (input_path: str) -> Tuple[Token, Weights]:
    lines = []
    with open(input_path, mode="r") as infile:
        lines = lex(infile.read())

    # The model type should be first; we should look for it
    model_type = lines[0][0]

    model: Weights = []
    inside_module = False
    for i in range(0, len(lines)):
        line = lines[i]
        transition: List[float] = []
        for j in range(len(line)):
            token = line[j]
            # This dummy EOL token should be of type TokenType.OTHER
            next_token = Token("EOL") if j >= (len(line) - 1) else line[j+1]

            # Don't touch weights outside of a module spec;
            # this ensures that we don't try to extract weights from a rewards spec or something
            if token.tokentype == TokenType.MODULE:
                inside_module = True
            if token.tokentype == TokenType.ENDMODULE:
                inside_module = False

            # Append the parsed weight
            # Weights for DTMC/MDP models are always followed by a colon,
            # and though this is a hacky check, it should be robust enough...
            if token.tokentype == TokenType.NUM and next_token.tokentype == TokenType.COLON and inside_module:
                transition.append(float(token.value))
        if len(transition) > 0:
            model.append(transition)
    return model_type, model

# Replace the weights of a supplied DTMC/MDP model file with a new set of weights
def patch_model (original: str, new_transitions: Weights, output_path: str):
    line_index = 0
    inside_module = False
    lines = []
    with open(original, mode="r") as infile:
        lines = lex(infile.read())
    for i in range(len(lines)):
        line = lines[i]
        weight_index = 0
        for j in range(len(line) - 1):
            token = line[j]
            # This dummy EOL token should be of type TokenType.OTHER
            next_token = Token("EOL") if j >= (len(line) - 1) else line[j+1]

            # Don't touch weights outside of a module spec;
            # this ensures that we don't try to extract weights from a rewards spec or something
            if token.tokentype == TokenType.MODULE:
                inside_module = True
            if token.tokentype == TokenType.ENDMODULE:
                inside_module = False

            # Replace the existing weight tokens with our new weights
            if token.tokentype == TokenType.NUM and next_token.tokentype == TokenType.COLON and inside_module:
                # ...unless we've already overread. Then we continue until error to see how much we've overread.
                if weight_index < len(new_transitions[line_index]) and line_index < len(new_transitions):
                    lines[i][j] = Token(f"{new_transitions[line_index][weight_index]}")
                weight_index += 1
        # Line had no weights in it, look for the next line
        if weight_index == 0:
            pass
        elif weight_index != len(new_transitions[line_index]):
            raise Exception(f"Wrong number of weights found on line {i} (expected {len(new_transitions)}, got {line_index})")
        else:
            line_index += 1
        weight_index = 0
    if line_index != len(new_transitions):
        raise Exception(f"Wrong number of transitions found in file (expected {len(new_transitions)}, got {line_index})")

    with open(output_path, mode="w+") as outfile:
        for line in lines:
            for token in line:
                outfile.write(f"{token.value} ")
            outfile.write("\n")

def parse_args ():
    argparser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description="Probabilistically average Prism model files"
    )
    argparser.add_argument("model_path")
    argparser.add_argument(
        "-q", "--query-path",
        help="""
            Path to the PCTL query to use (if not supplied, ask for a query during runtime)
            """,
        default=""
    )
    argparser.add_argument(
        "-u", "--uncertainty",
        help="""
            The possible uncertainty range for each submodel (default=0.01)
            """,
        default=0.01
    )
    argparser.add_argument(
        "-n", "--num-submodels",
        help="""
            The number of submodels to calculate for this model (default=3)
            """,
        default=3
    )
    argparser.add_argument(
        "-s", "--skew-models",
        help="""
            Additionally, take this many skews of each submodel (default=0)
            """,
        default=0
    )
    argparser.add_argument(
        "-d", "--delta-skew",
        help="""
            If model skewing is enabled, the maximum amount of skew (default=0.005)
            """,
        default=0.005
    )
    argparser.add_argument(
        "-a", "--average-models",
        help="""
            Pick this many values for each submodel (default=1)
            """,
        default=0
    )
    argparser.color = False
    if len(sys.argv) < 2:
        argparser.print_usage()
        exit(1) # Fail
    args = argparser.parse_args()
    if not os.path.isfile(args.model_path):
        print(f"error: model file {args.model_path} not found")
        exit(1)
    if args.query_path != "" and not os.path.isfile(args.query_path):
        print(f"error: query file {args.query_path} not found")
        exit(1)
    return args

if __name__ == "__main__":
    args = parse_args()

    model_path = args.model_path
    model_type, weights = read_model(model_path)

    # This tool only supports DTMC, CTMC, and MDP
    continuous_time = False
    match model_type.tokentype:
        case TokenType.CTMC:
            continuous_time = True
        case TokenType.DTMC:
            continuous_time = False
        case TokenType.MDP:
            continuous_time = False
        case _:
            print(f"error: unrecognized model type {model_type.value}")
            exit(1)

    # Sanity check: If there are no weights to parse in the original file,
    # the program will fail to do anything because there is nothing to do
    # Check to see if there are even any weights to manipulate
    if len(weights) == 0:
        print(f"error: no weights present to manipulate")
        exit(1)

    # Another sanity check: The parser may miss a weight in the original file
    # If this happens, the program would otherwise just blindly keep trying,
    # not knowing that it might be impossible to generate a suitable model
    # This should prevent that by validating the original model
    for i in range(len(weights)):
        transition = weights[i]
        if sum(transition) != 1:
            print(f"error: transition {i} of original model has invalid weights (sums to {sum(transition)} instead of 1)")
            exit(1)

    # Request user PCTL query
    if args.query_path == "":
        query_by_path = False
        query_string = input("Enter PCTL query: ")
    else:
        query_by_path = True
        query_string = ""

    print("Generating submodels...", end=" ")
    if continuous_time:
        submodels = generate_uncertain_submodels_ctmc(
        weights,
        uncertainty=float(args.uncertainty) / 2,
        num_subintervals=int(args.num_submodels))
    else:
        submodels = generate_uncertain_submodels(
            weights,
            uncertainty=float(args.uncertainty) / 2,
            num_subintervals=int(args.num_submodels))
    print("[Done]")

    # TODO: Maybe put each submodel alongside its skew
    print("Applying skew...", end=" ")
    unskewed = submodels.copy()
    for submodel in unskewed:
        for _ in range(int(args.skew_models)):
            submodels.append(skew_uncertain_model(submodel, max_offset=float(args.delta_skew)))
    print("[Done]")

    # TODO: Multiprocessing would probably make this considerably faster
    print("Querying submodels...")
    raw_results: List = []
    for i in range(len(submodels)):
        submodel = submodels[i]
        # Pick some random samples from each submodel, and average them
        decided_models: List[Weights] = []
        for _ in range(int(args.average_models)):
            decided_models.append(decide_submodel(submodel, precision=ROUNDING_PRECISION))
        model = average_models(decided_models)
        # Run the PCTL query on the new model
        patch_model(model_path, model, MODEL_TEMPFILE_NAME)
        if query_by_path:
            returncode = prism.query_dtmc_with_file(MODEL_TEMPFILE_NAME, args.query_path, RESULT_TEMPFILE_NAME)
        else:
            returncode = prism.query_dtmc(MODEL_TEMPFILE_NAME, query_string, RESULT_TEMPFILE_NAME)
        if returncode != 0:
            print(f"error: prism query failed with exit code {returncode}")
            exit(1)
        subresult = pd.read_csv(RESULT_TEMPFILE_NAME)
        os.remove(MODEL_TEMPFILE_NAME)
        os.remove(RESULT_TEMPFILE_NAME)
        # Take the mean results
        raw_results.append(subresult)
        print(f"- [{i+1}/{len(submodels)}]")
    results = pd.concat(raw_results, ignore_index=True)
    print("Querying submodels... [Done]")
    
    # Run MCMC on the submodel; actually, run MCMC on each query result
    # as sometimes there may be multiple results from one query... maybe
    keys = []
    means = []
    stdevs = []
    cis = []
    print(f"Calculating statistical results (MCMC)...", end=" ")
    for key, series in results.items():
        mcmc_input = series.to_list()
        mean, stdev, ci = mcmc(mcmc_input)
        keys.append(key)
        means.append(mean)
        stdevs.append(stdev)
        cis.append(ci)
    print("[Done]")

    results = pd.DataFrame({"mean": means, "stdev": stdevs, "conf_int": cis}, index=keys)
    print(results)
    results.to_csv("data/results.csv")
