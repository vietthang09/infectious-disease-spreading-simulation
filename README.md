# Infectious Disease Spreading Simulation — Task 2

This repository contains a reproducible cellular-automaton experiment for
studying how death probability `d` and recovery/immunity probability `s = 1-d`
affect epidemic duration and total deaths.

## Model used by Task 2

- Grid: 60 × 40 with periodic boundaries.
- Population: 800 agents; one starts Infected and all others start Healthy.
- Infection probability per Sick neighbour: `p = 0.3`.
- Incubation duration: 5 steps.
- Infectious/Sick duration: 5 steps.
- At the end of the Sick period an agent dies with probability `d`, otherwise
  it becomes immune/recovered with probability `s = 1-d`.
- Experiment range: `d = 0.0, 0.1, ..., 0.9`.
- Repetitions: five fixed random seeds per value of `d`.
- A run ends when no Infected or Sick agents remain. The 1,000-step safety
  limit is recorded explicitly if reached.

The death/recovery decision occurs after the same fixed infectious duration.
Consequently, `d` affects later spatial dynamics because dead agents leave an
empty cell while recovered agents continue occupying a cell; it does not make
an individual stop being infectious earlier.

## Setup

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the complete Task 2 experiment

```bash
python task2_experiment.py
```

This creates:

- `results/task2_raw_runs.csv`: one row per seed and `d` value.
- `results/task2_summary.csv`: mean and standard deviation by `d`.
- `plots/task2_duration_vs_d.png`.
- `plots/task2_deaths_vs_d.png`.

Custom ranges can also be used, for example:

```bash
python task2_experiment.py --d-start 0.0 --d-end 0.5 --d-step 0.1
```

## Interactive animation

```bash
python main.py
```

The interface can animate one selected `(d, seed)` run in slow or fast mode,
or execute the complete batch. Batch results are saved to the same output
directories.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover the initial condition, incubation timing, `d=0` and `d=1`
outcomes, population conservation, reproducibility, and parameter validation.

The final interpretation of the experiment is in
[`report/task2_report.md`](report/task2_report.md).
