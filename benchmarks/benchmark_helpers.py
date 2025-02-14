from collections import defaultdict
from glob import iglob

import argparse
import os
import sys

sys.path.append("..")

from lib.algorithms import PathFormulation, TEAVAR
from lib.algorithms.abstract_formulation import OBJ_STRS
from lib.partitioning import FMPartitioning, SpectralClustering

PROBLEM_NAMES = [
    "GtsCe.graphml",
    "UsCarrier.graphml",
    "Cogentco.graphml",
    "Colt.graphml",
    "TataNld.graphml",
    "Deltacom.graphml",
    "DialtelecomCz.graphml",
    "Kdl.graphml",
]
TM_MODELS = [
    "uniform",
    "gravity",
    "bimodal",
    "poisson-high-intra",
    "poisson-high-inter",
]
SCALE_FACTORS = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0]

PATH_FORM_HYPERPARAMS = (4, True, "inv-cap")
NCFLOW_HYPERPARAMS = {
    "GtsCe.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "UsCarrier.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "Cogentco.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "Colt.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "TataNld.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "Deltacom.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "DialtelecomCz.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "Uninett2010.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "Interoute.graphml": (4, True, "inv-cap", SpectralClustering, 2),
    "Ion.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "Kdl.graphml": (4, True, "inv-cap", FMPartitioning, 3),
    "erdos-renyi-1260231677.json": (4, True, "inv-cap", FMPartitioning, 3),
}

PROBLEM_NAMES_AND_TM_MODELS = [
    (prob_name, tm_model) for prob_name in PROBLEM_NAMES for tm_model in TM_MODELS
]

PROBLEMS = []
GROUPED_BY_PROBLEMS = defaultdict(list)
HOLDOUT_PROBLEMS = []
GROUPED_BY_HOLDOUT_PROBLEMS = defaultdict(list)

for problem_name in PROBLEM_NAMES:
    if problem_name.endswith(".graphml"):
        topo_fname = os.path.join("..", "topologies", "topology-zoo", problem_name)
    else:
        topo_fname = os.path.join("..", "topologies", problem_name)
    for model in TM_MODELS:
        for tm_fname in iglob(
            "../traffic-matrices/{}/{}*_traffic-matrix.pkl".format(model, problem_name)
        ):
            vals = os.path.basename(tm_fname)[:-4].split("_")
            _, traffic_seed, scale_factor = vals[1], int(vals[2]), float(vals[3])
            GROUPED_BY_PROBLEMS[(problem_name, model, scale_factor)].append(
                (topo_fname, tm_fname)
            )
            PROBLEMS.append((problem_name, topo_fname, tm_fname))
        for tm_fname in iglob(
            "../traffic-matrices/holdout/{}/{}*_traffic-matrix.pkl".format(
                model, problem_name
            )
        ):
            vals = os.path.basename(tm_fname)[:-4].split("_")
            _, traffic_seed, scale_factor = vals[1], int(vals[2]), float(vals[3])
            GROUPED_BY_HOLDOUT_PROBLEMS[(problem_name, model, scale_factor)].append(
                (topo_fname, tm_fname)
            )
            HOLDOUT_PROBLEMS.append((problem_name, topo_fname, tm_fname))

GROUPED_BY_PROBLEMS = dict(GROUPED_BY_PROBLEMS)
for key, vals in GROUPED_BY_PROBLEMS.items():
    GROUPED_BY_PROBLEMS[key] = sorted(vals)

GROUPED_BY_HOLDOUT_PROBLEMS = dict(GROUPED_BY_HOLDOUT_PROBLEMS)
for key, vals in GROUPED_BY_HOLDOUT_PROBLEMS.items():
    GROUPED_BY_HOLDOUT_PROBLEMS[key] = sorted(vals)


# This should be called when `many_problems` is False
def get_problem(args):
    topo_fname, tm_fname = GROUPED_BY_PROBLEMS[
        (args.topo, args.tm_model, args.scale_factor)
    ][args.slice]
    return [(args.topo, topo_fname, tm_fname)]


# This should be called when `many_problems` is True
def get_problems(args):
    problems = []
    for (
        (problem_name, tm_model, scale_factor),
        topo_and_tm_fnames,
    ) in GROUPED_BY_PROBLEMS.items():
        for slice in args.slices:
            if (
                ("all" in args.topos or problem_name in args.topos)
                and ("all" in args.tm_models or tm_model in args.tm_models)
                and ("all" in args.scale_factors or scale_factor in args.scale_factors)
            ):
                topo_fname, tm_fname = topo_and_tm_fnames[slice]
                problems.append((problem_name, topo_fname, tm_fname))
    return problems


class AlgoClsAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        if value == "PathFormulation":
            value = PathFormulation
        elif value == "TEAVAR":
            value = TEAVAR
        setattr(namespace, self.dest, value)


def get_args_and_problems(
    formatted_fname_template,
    additional_args=[],
    *,
    many_problems=True,
):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    parser.add_argument(
        "--obj",
        type=str,
        choices=OBJ_STRS,
        required=True,
    )
    if many_problems:
        parser.add_argument(
            "--tm-models",
            type=str,
            choices=TM_MODELS + ["all"],
            nargs="+",
            default="all",
        )
        parser.add_argument(
            "--topos",
            type=str,
            choices=PROBLEM_NAMES + ["all"],
            nargs="+",
            default="all",
        )
        parser.add_argument(
            "--scale-factors",
            type=lambda x: x if x == "all" else float(x),
            choices=SCALE_FACTORS + ["all"],
            nargs="+",
            default="all",
        )
        parser.add_argument(
            "--slices", type=int, choices=range(5), nargs="+", required=True
        )
    else:
        parser.add_argument("--tm-model", type=str, choices=TM_MODELS, required=True)
        parser.add_argument("--topo", type=str, choices=PROBLEM_NAMES, required=True)
        parser.add_argument(
            "--scale-factor", type=float, choices=SCALE_FACTORS, required=True
        )
        parser.add_argument("--slice", type=int, choices=range(5), required=True)

    for add_arg in additional_args:
        name_or_flags, kwargs = add_arg[0], add_arg[1]
        parser.add_argument(name_or_flags, **kwargs)
    args = parser.parse_args()
    if many_problems:
        slice_str = "slice_" + "_".join(str(i) for i in args.slices)
        formatted_fname_substr = formatted_fname_template.format(args.obj, slice_str)
        return args, formatted_fname_substr, get_problems(args)
    else:
        formatted_fname_substr = format_args_for_filename(
            formatted_fname_template, args, additional_args
        )
        return args, formatted_fname_substr, get_problem(args)


# Should only be used when `many_problems` is False
def format_args_for_filename(template, args, additional_args):
    slice_str = "slice_{}".format(args.slice)
    additional_info_str = "problem_{}-tm_model_{}-scale_factor_{}".format(
        args.topo, args.tm_model, args.scale_factor
    )
    args_as_dict = vars(args)
    for add_arg in additional_args:
        add_arg_formatted = add_arg[0][2:].replace("-", "_")
        additional_info_str += "-{}_{}".format(
            add_arg_formatted, args_as_dict[add_arg_formatted]
        )
    formatted_string = template.format(args.obj, slice_str + "_" + additional_info_str)

    return formatted_string


def print_(*args, file=None):
    if file is None:
        file = sys.stdout
    print(*args, file=file)
    file.flush()
