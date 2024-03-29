import argparse
import timeit
import json
import pickle

import config.cofig
from reduct_matrix import get_reduct_matrix
from evaluator import run_evaluation
from config.cofig import PROJECT_DIR


def save_results(evaluation_results, config_file, t, n, d, dataset):
    config_name = config_file.split('/')[-1].split('.')[0]
    with open(f"{PROJECT_DIR}/tuning/results_{dataset}_{config_name}_t_{t}_n_{n}_d_{d}.pickle", "wb") as f:
        pickle.dump(evaluation_results, f)

    with open(f"{PROJECT_DIR}/tuning/results_{dataset}_{config_name}_t_{t}_n_{n}_d_{d}.json", "w") as f:
        json.dump(evaluation_results[0], f)


def analyze_results(evaluation_results):
    results_list = evaluation_results[0]
    best_result = max(results_list, key=lambda x: x[1]["Total reward mean"])
    print(f"Best result is {best_result}")
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--trials",
        metavar="TRIALS",
        type=int,
        help="Number of trials",
        required=True,
    )

    parser.add_argument(
        "-d",
        "--dimension",
        type=int,
        help="Dimension of reduction matrix",
        required=True,
    )

    parser.add_argument(
        "--num-rep",
        type=int,
        help="Number of repetitions for each algorithms, default = 5",
        default=5,
    )

    parser.add_argument(
        "--load-old-reduct-matrix",
        dest="load_old_reduct_matrix",
        action="store_true",
        default=False,
        help="Load reduction matrix of needed dimension from file. "
             "Will throw error if no file exists."
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Config file for parameter tuning",
    )

    parser.add_argument(
        '--data',
        dest="dataset_type",
        type=str,
        default="amazon",
        help="Which data to use, 'amazon', 'movielens' or 'jester'",
    )

    parser.add_argument(
        "-f",
        "--feature-flag",
        dest="feature_flag",
        action="store_true",
        default=False,
        help="General feature flag, used to test new features",
    )

    parser.add_argument(
        "--tune",
        dest="tune",
        action="store_true",
        default=False,
        help="Use separate subset of data for tuning",
    )

    parser.add_argument(
        "--non-stationarity",
        dest="non_stationarity",
        action="store_true",
        default=False,
        help="Introduce non-stationarity into the evaluation",
    )

    parser.add_argument(
        "--intervals",
        dest="intervals",
        type=str,
        default="[]",
        help="Intervals to use for non-stationarity",
    )

    parser.add_argument(
        "--wandb",
        dest="wandb",
        action="store_true",
        default=False,
        help="Log the experiment to wandb",
    )

    args = parser.parse_args()

    if args.dataset_type not in ["amazon", "movielens", "jester"]:
        raise ValueError("--data should be in ['movielens', 'jester']")

    if args.wandb:
        config.cofig.WANDB_LOGGING = True


    intervals = json.loads(args.intervals)
    if intervals:
        config.cofig.NON_STATIONARITY_INTERVALS = intervals

    reduct_matrix = get_reduct_matrix(args.dataset_type, args.dimension, args.load_old_reduct_matrix)

    timeBegin = timeit.default_timer()
    evaluation_results = run_evaluation(
        args.trials, args.num_rep, reduct_matrix, args.config,
        dataset_type=args.dataset_type, feature_flag=args.feature_flag,
        tune=args.tune, non_stationarity=args.non_stationarity,
    )

    print("Saving results")
    save_results(evaluation_results, args.config, args.trials, args.num_rep, args.dimension, args.dataset_type)

    timeEnd = timeit.default_timer()
    print(f"Done.\nThe whole experiment took {timeEnd - timeBegin:.2f} seconds.")

    analyze_results(evaluation_results)


