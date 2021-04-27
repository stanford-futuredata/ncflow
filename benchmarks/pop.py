#! /usr/bin/env python

import traceback
import pickle
import os
from itertools import product
from benchmark_consts import get_args_and_problems, print_, PATH_FORM_HYPERPARAMS

import sys

sys.path.append("..")

from lib.algorithms import POP
from lib.problem import Problem


TOP_DIR = "pop-logs"
OUTPUT_CSV = "pop.csv"

# Sweep topos and traffic matrices for that topo. For each combo, record the
# runtime and total flow for each algorithm
HEADERS = [
    "problem",
    "num_nodes",
    "num_edges",
    "traffic_seed",
    "tm_model",
    "scale_factor",
    "num_commodities",
    "total_demand",
    "algo",
    "split_method",
    "num_subproblems",
    "num_paths",
    "edge_disjoint",
    "dist_metric",
    "objective",
    "obj_val",
    "runtime",
]
PLACEHOLDER = ",".join("{}" for _ in HEADERS)


def benchmark(problems):

    with open(OUTPUT_CSV, "a") as results:
        print_(",".join(HEADERS), file=results)
        for problem_name, topo_fname, tm_fname in problems:
            problem = Problem.from_file(topo_fname, tm_fname)
            print_(problem.name, tm_fname)
            traffic_seed = problem.traffic_matrix.seed
            total_demand = problem.total_demand
            print_("traffic seed: {}".format(traffic_seed))
            print_("traffic matrix model: {}".format(problem.traffic_matrix.model))
            print_(
                "traffic matrix scale factor: {}".format(
                    problem.traffic_matrix.scale_factor
                )
            )
            print_("total demand: {}".format(total_demand))

            num_paths, edge_disjoint, dist_metric = PATH_FORM_HYPERPARAMS

            NUM_SUBPROBLEMS_SWEEP = [2, 4, 8, 16, 32, 64]
            SPLIT_METHODS_SWEEP = ["tailored", "skewed", "random", "means", "covs"]
            for num_subproblems, split_method in product(
                NUM_SUBPROBLEMS_SWEEP, SPLIT_METHODS_SWEEP
            ):
                run_dir = os.path.join(
                    TOP_DIR,
                    problem.name,
                    "{}-{}".format(traffic_seed, problem.traffic_matrix.model),
                )
                if not os.path.exists(run_dir):
                    os.makedirs(run_dir)

                try:
                    print_(
                        "\nPOP, {} split method, {} subproblems, {} paths, edge disjoint {}, dist metric {}".format(
                            split_method,
                            num_subproblems,
                            num_paths,
                            edge_disjoint,
                            dist_metric,
                        )
                    )
                    run_pop_dir = os.path.join(
                        run_dir,
                        "pop",
                        split_method,
                        "{}-partitions".format(num_subproblems),
                        "{}-paths".format(num_paths),
                        "edge_disjoint-{}".format(edge_disjoint),
                        "dist_metric-{}".format(dist_metric),
                    )
                    if not os.path.exists(run_pop_dir):
                        os.makedirs(run_pop_dir)
                    with open(
                        os.path.join(
                            run_pop_dir,
                            "{}-pop-split-method_{}-{}_partitions-{}_paths-edge_disjoint_{}-dist_metric_{}.txt".format(
                                problem.name,
                                split_method,
                                num_subproblems,
                                num_paths,
                                edge_disjoint,
                                dist_metric,
                            ),
                        ),
                        "w",
                    ) as log:
                        pop = POP.new_max_flow(
                            num_subproblems,
                            split_method,
                            num_paths=num_paths,
                            edge_disjoint=edge_disjoint,
                            dist_metric=dist_metric,
                            out=log,
                        )
                        pop.solve(problem)
                        sol_dict = pop.sol_dict
                        with open(log.name.replace(".txt", "-sol-dict.pkl"), "wb") as w:
                            pickle.dump(sol_dict, w)

                        result_line = PLACEHOLDER.format(
                            problem_name,
                            len(problem.G.nodes),
                            len(problem.G.edges),
                            traffic_seed,
                            problem.traffic_matrix.model,
                            problem.traffic_matrix.scale_factor,
                            len(problem.commodity_list),
                            total_demand,
                            "pop",
                            split_method,
                            num_subproblems,
                            num_paths,
                            edge_disjoint,
                            dist_metric,
                            "max_flow",
                            pop.obj_val,
                            pop.runtime_est(28),  # hard-coded for DAWN machines
                        )
                        print_(result_line, file=results)

                except:
                    print_(
                        "POP split method {}, {} subproblems, {} paths, Problem {}, traffic seed {}, traffic model {} failed".format(
                            split_method,
                            num_subproblems,
                            num_paths,
                            problem.name,
                            traffic_seed,
                            problem.traffic_matrix.model,
                        )
                    )
                    traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    if not os.path.exists(TOP_DIR):
        os.makedirs(TOP_DIR)

    args, problems = get_args_and_problems()

    if args.dry_run:
        print("Problems to run:")
        for problem in problems:
            print(problem)
    else:
        benchmark(problems)