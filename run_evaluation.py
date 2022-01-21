import argparse
import numpy as np
import timeit

from data_loading import get_r6b_data, get_r6b_pickle_data, get_movielens_data
from evaluation import evaluate_policy_on_r6b, evaluate_policy_on_movielens
from policies import policy_generation
from reduct_matrix import get_reduct_matrix


def run_evaluation(trials, num_rep, reduct_matrix, dataset_type):
    print(f"Running each algorithm for {num_rep} repetitions")
    if dataset_type == "r6b":
        data = get_r6b_pickle_data()
    elif dataset_type == "movielens":
        data = get_movielens_data()
    else:
        raise ValueError(f"Unknown dataset type {dataset_type}")

    times = trials
    # conduct analyses
    experiment_bandit = ['BCMABRP', 'CBRAP', 'LinearTS', 'LinUCB', 'random']
    results = {}
    cum_reward = {}
    cum_ctr = {}
    time_all_dict = {}

    i = 0
    for bandit_name in experiment_bandit:
        print(bandit_name)
        reward_all, ctr_all, final_rew_all, time_all = [], [], [], []
        for j in range(num_rep):
            timeBegin = timeit.default_timer()

            policy = policy_generation(bandit_name, reduct_matrix)
            if dataset_type == "r6b":
                seq_reward, seq_ctr = evaluate_policy_on_r6b(policy, bandit_name, data, times)
            elif dataset_type == "movielens":
                # TODO Implement movielens evaluation
                streaming_batch, user_feature, actions, reward_list, action_context = data
                action_features = None
                seq_reward = evaluate_policy_on_movielens(policy, bandit_name, streaming_batch, user_feature, reward_list,
                                              actions, action_features, times)
                seq_ctr = None

            timeEnd = timeit.default_timer()

            reward_all.append(seq_reward)
            ctr_all.append(seq_ctr)
            time_all.append(timeEnd - timeBegin)
            final_rew_all.append(seq_reward[times - 1])

        results[bandit_name] = [np.mean(time_all)]
        results[bandit_name].append(np.mean(final_rew_all))  # average of final regret for n rep
        results[bandit_name].append(np.var(final_rew_all))

        time_all_dict[bandit_name] = time_all
        cum_reward[bandit_name] = reward_all
        cum_ctr[bandit_name] = ctr_all

    print("Done!")
    return results, cum_reward, cum_ctr, time_all_dict


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

    args = parser.parse_args()

    reduct_matrix = get_reduct_matrix(args.dimension, args.load_old_reduct_matrix)

    run_evaluation(args.trials, args.num_rep, reduct_matrix, dataset_type="r6b")