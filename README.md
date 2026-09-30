 ### PySIMUS: Statistical Inference on Model Checking of Uncertain Stochastic Structures

PySIMUS is a tool that calculates the outcomes of a Markov Chain or Markov Decision Process. It uses various methods to reduce bias towards one particular result. It automatically detects the model type, and supports DTMC, CTMC, and MDP models with single-probability weights.

---

## How It Works

PySIMUS operates in three stages.

First, it takes an input model file with single-probability weights and converts each weight into an interval. The size of each interval can be specified here. The intervals are then split into subintervals, which are then combined into submodels. For each submodel, the original weight in the original model is replaced with a subinterval, ensuring that any constraints on the weights themselves are satisfied. The number of subintervals (and thus, the number of submodels) can be specified here.

Second, it gathers a sampling of random single-probability weights from each submodel and forms new models based on the original. The number of samplings performed for each submodel is specified here. If taking skewed submodels, whose interval probabilities are all offset by some amount, it will do those here too. Whether to use skewed submodels, how many skewings to take of each submodel, and the maximum amount to skew by, can all be specified here.

Finally, the new models are passed alongside a user-specified PCTL query to PRISM Model Checker, and the results are then fed into Markov Chain Monte Carlo to generate a probability distribution.

---

## Setup

The tool requires some external dependencies. Notably, you need to install Java (version 11 or higher) and Python (version 3.14 or higher). Some initial setup is required before you can run the tool, but you do not need to repeat this setup on subsequent uses. To perform the initial setup for the environment in which you have to run this tool, do the following, depending on your operating system:

### Windows

1. Follow [these instructions](https://www.prismmodelchecker.org/download.php) to install PRISM Model Checker for whichever operating system you're using. If you are able, it's advised you install it in `bin\prism` (the path `bin\prism\bin\prism` should exist).
2. Open Powershell in this folder, and run the following commands in order:
    1. `python -m venv bin\pyvenv` to create a Python virtual environment
    2. `. bin\pyvenv\bin\Activate.ps1` to enter the virtual environment
    3. `pip install -r requirements.txt` to install PySIMUS's Python dependencies

### MacOS/Linux

1. Follow [these instructions](https://www.prismmodelchecker.org/download.php) to install PRISM Model Checker for whichever operating system you're using. If you are able, it's advised you install it in `bin/prism` (the path `bin/prism/bin/prism` should exist).
2. Open a terminal in this directory, and run the following commands in order:
    1. `python -m venv bin/pyvenv` to create a Python virtual environment
    2. `source bin/pyvenv/bin/activate` to enter the virtual environment
    3. `pip install -r requirements.txt` to install PySIMUS's Python dependencies

### Subsequent Uses

After this initial setup, you will need to enter the virtual environment on each subsequent usage of the tool.

- On Windows, run `. bin\pyvenv\bin\Activate.ps1`
- On MacOS or Linux, run `source bin/pyvenv/bin/activate`

---

## Usage

Assuming you have done the necessary setup, to run PySIMUS on a PRISM-format MDP model, open Powershell/a terminal in this folder/directory and run the following command: `python main.py <input filename> [additional options]`

The most useful additional options include:
- `-u/--uncertainty`: Controls the size of the intervals surrounding each weight during the interval selection process. If not specified, a default of 0.05 is used for all model types.
- `-n/--num-submodels`: Controls the number of subintervals formed during the interval selection process. This directly controls the number of submodels taken. If not specified, a default of 3 is used for all model types.
- `-a/--average-models`: Controls the number of weights to generate from each interval during the weight generation process. If not specified, a default of 1 is used.

You may also run `main.py -h` or `main.py --help` for a comprehensive list of additional options and how to use them.

### Query Formatting

Queries to the model are to be specified as PCTL queries. You may enter one when the tool first starts, or pass one as a PCTL file via the `-q/--query-file` option. The tool only supports using one query at a time.

A guide to formatting PCTL queries can be found here: [www.prismmodelchecker.org/manual/PropertySpecification/Introduction](https://www.prismmodelchecker.org/manual/PropertySpecification/Introduction)

<!-- TODO: Could probably be more comprehensive than this -->
