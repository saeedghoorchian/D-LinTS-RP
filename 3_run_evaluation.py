import argparse
import timeit
import json
import pickle

from evaluator import run_evaluation
from reduct_matrix import get_reduct_matrix
from config.cofig import PROJECT_DIR

EVALUATION_CONFIG_FILE = "config/evaluation.json"


def save_results(results, config_file, t, n, d, dataset):
    config_name = config_file.split('/')[-1].split('.')[0]
    with open(f"{PROJECT_DIR}/results/results_{dataset}_{config_name}_t_{t}_n_{n}_d_{d}.pickle", "wb") as f:
        pickle.dump(results, f)

    with open(f"{PROJECT_DIR}/results/results_{dataset}_{config_name}_t_{t}_n_{n}_d_{d}.json", "w") as f:
        json.dump(results[0], f)


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
        '--data',
        dest="dataset_type",
        type=str,
        default="amazon",
        help="Which data to use, 'amazon', 'movielens' or 'jester'",
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Config file for evaluation",
    )

    args = parser.parse_args()

    if args.dataset_type not in ["amazon", "movielens", "jester"]:
        raise ValueError("--data should be in ['movielens', 'jester']")

    reduct_matrix = get_reduct_matrix(args.dataset_type, args.dimension, args.load_old_reduct_matrix)

    timeBegin = timeit.default_timer()

    evaluation_results = run_evaluation(
        args.trials, args.num_rep, reduct_matrix, args.config,
        dataset_type=args.dataset_type, feature_flag=False,
        tune=False, non_stationarity=True,
    )

    print("Saving results")
    save_results(evaluation_results, args.config, args.trials, args.num_rep, args.dimension, args.dataset_type)

    timeEnd = timeit.default_timer()
    print(f"Done.\nThe whole experiment took {timeEnd - timeBegin:.2f} seconds.")


