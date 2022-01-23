import argparse
import timeit
import json
import pickle

from reduct_matrix import get_reduct_matrix
from evaluator import run_evaluation
from config.cofig import PROJECT_DIR


def save_results(evaluation_results, config_file, t, n, d):
    with open(f"{PROJECT_DIR}/tuning/results_{config_file.split('.')[0]}_t_{t}_n_{n}_d_{d}.pickle", "wb") as f:
        pickle.dump(evaluation_results, f)

    with open(f"{PROJECT_DIR}/tuning/results_t_{t}_n_{n}_d_{d}.json", "w") as f:
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

    args = parser.parse_args()

    reduct_matrix = get_reduct_matrix(args.dimension, args.load_old_reduct_matrix)

    timeBegin = timeit.default_timer()
    evaluation_results = run_evaluation(args.trials, args.num_rep, reduct_matrix, args.config, dataset_type="movie")

    print("Saving results")
    save_results(evaluation_results, args.config, args.trials, args.num_rep, args.dimension)

    timeEnd = timeit.default_timer()
    print(f"Done.\nThe whole experiment took {timeEnd - timeBegin:.2f} seconds.")

    analyze_results(evaluation_results)

