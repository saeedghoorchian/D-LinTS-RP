from datetime import datetime
import numpy as np
import pandas as pd
import time


class RecommenderDataset:
    def __init__(
        self,
        actions,
        action_features,
        action_biases,
        user_stream,
        true_user_features,
        user_features,
        user_biases,
        reward_list,
        ratings_list,
        ratings_range,
        implicit_feedback,  # If implicit feedback estimate unseen ratings as 0 for NDCG.
        test_user_ids,
        times,
        n_arms,
        tune,
        shift_back=False,
    ):
        self.shift_back = shift_back
        start_ts = time.time()
        self.actions: list = actions
        self.actions_index_by_action_id = {
            a_id: ind for ind, a_id in enumerate(self.actions)
        }
        self.action_features: pd.DataFrame = action_features
        self.action_biases: pd.DataFrame = action_biases

        self.user_stream: pd.DataFrame = user_stream
        # User features present in the data. Used in the MovieLens experiment.
        self.true_user_features: pd.DataFrame = true_user_features
        # User features extracted by the SVD.
        self.user_features: pd.DataFrame = user_features
        self.user_biases: pd.DataFrame = user_biases

        self.reward_list: pd.DataFrame = reward_list
        self.ratings_list: pd.DataFrame = ratings_list
        self.ratings_range: tuple = ratings_range
        self.implicit_feedback: bool = implicit_feedback
        self.test_user_ids: set = test_user_ids or set()

        # Don't use test users for training.
        self.user_stream = self.user_stream[~ self.user_stream.user_id.isin(self.test_user_ids)]

        # Split a separate tuning set. Use 30k users previous to the train set.
        tune_ind = self.user_stream.index[-130000:-100000]

        self.tune_user_stream = self.user_stream.loc[tune_ind]
        self.eval_user_stream = self.user_stream.loc[list(set(self.user_stream.index) - set(tune_ind))]

        (
            self.action_context_dict,
            self.action_bias_dict,
            self.true_user_features_array,
            self.user_features_array,
            self.user_biases_array,
            self.user_id_to_index,
            self.watched_list_series,
            self.reward_matrix,
            self.user_id_to_watched_list_index,
            self.user_item_to_rating,
        ) = self.data_preprocessing()

        # self.test_users_data = self.generate_test_users()

        # self.exp_reward_matrix = self.generate_experiment_reward_matrix(times, n_arms, tune)
        # exp_mean_rewards = np.mean(self.exp_reward_matrix, axis=0)
        # # Sort actions based on experiment mean rewards.
        # self.actions = [x for _, x in sorted(zip(exp_mean_rewards, self.actions), key=lambda pair: pair[0], reverse=True)]
        #
        # # Re-create the reward matrix for sorted actions.
        # self.reward_matrix = np.zeros((len(self.user_id_to_watched_list_index), len(self.actions)))
        # for uid, ind in self.user_id_to_watched_list_index.items():
        #     watched_list = self.watched_list_series.iloc[ind]
        #     watched_indices = [i for i in range(len(self.actions)) if self.actions[i] in watched_list]
        #     # Binary vector of rewards for each arm.
        #     self.reward_matrix[ind, watched_indices] = 1
        #
        # # Re-create exp reward matrix
        # self.exp_reward_matrix = self.generate_experiment_reward_matrix(times, n_arms, tune)

        print(f"Dataset creation took {time.time() - start_ts} s.")

    def data_preprocessing(self):
        """Preprocess the data to be in a format that allows more optimal policy evaluation.
        This method reindexes true_user_features, user_features, user_biases and reward_list.
        """
        action_context_dict = {}
        action_bias_dict = {}
        for action_id in self.actions:
            action_context = np.array(
                self.action_features[self.action_features["item_id"] == action_id]
            )[0][1:]
            action_bias = self.action_biases[
                self.action_biases["item_id"] == action_id
            ].iloc[0][1]
            action_context_dict[action_id] = action_context.astype(np.float64)
            action_bias_dict[action_id] = action_bias

        if "user_id" in self.true_user_features.columns:
            self.true_user_features = self.true_user_features.set_index("user_id")
        true_user_features_array = self.true_user_features.to_numpy(dtype=np.float32)

        self.user_features = self.user_features.set_index("user_id")
        self.user_features = self.user_features.reindex(self.true_user_features.index)
        user_features_array = self.user_features.to_numpy(dtype=np.float32)

        assert (
            self.user_features.index == self.true_user_features.index
        ).all(), "Indexes of user features and true u.f. dont coincide"

        self.user_biases = self.user_biases.set_index("user_id")
        self.user_biases = self.user_biases.reindex(self.user_features.index)
        user_biases_array = self.user_biases.to_numpy(dtype=np.float32)

        assert (
            self.user_features.index == self.user_biases.index
        ).all(), "Indexes of user features and biases dont coincide"

        # This is an optimization because pandas indexing is slower.
        user_id_to_index = {
            uid: ind for ind, uid in enumerate(self.user_features.index)
        }

        self.reward_list = self.reward_list.set_index("user_id")
        watched_list_series = (
            self.reward_list.groupby("user_id")["item_id"].agg(set=set).set
        )
        user_id_to_watched_list_index = {
            uid: ind for ind, uid in enumerate(watched_list_series.index)
        }

        reward_matrix = np.zeros((len(user_id_to_watched_list_index), len(self.actions)))
        for uid, ind in user_id_to_watched_list_index.items():
            watched_list = watched_list_series.iloc[ind]
            watched_indices = [i for i in range(len(self.actions)) if self.actions[i] in watched_list]
            # Binary vector of rewards for each arm.
            reward_matrix[ind, watched_indices] = 1

        if self.shift_back:
            # Remove some of the arms for Amazon data to reduce inherent non-stationarity.
            for j in [13, 14, 18, 27, 96]:
                reward_matrix[:, j] = 0

        user_item_to_rating = {}
        for (user_id, item_id, rating) in self.ratings_list.to_numpy():
            user_item_to_rating[(user_id, item_id)] = rating

        return (
            action_context_dict,
            action_bias_dict,
            true_user_features_array,
            user_features_array,
            user_biases_array,
            user_id_to_index,
            watched_list_series,
            reward_matrix,
            user_id_to_watched_list_index,
            user_item_to_rating,
        )

    # TODO Remove this function and everything that uses it.
    def get_full_data(self):
        """For legacy compatibility reasons"""
        return (
            self.actions,
            self.action_features,
            self.action_biases,
            self.user_stream,
            self.true_user_features,
            self.user_features,
            self.user_biases,
            self.reward_list,
            self.ratings_list,
        )

    def get_full_context(self, user_t):
        user_feature_index = self.user_id_to_index[user_t]
        true_user_feature = self.true_user_features_array[user_feature_index]

        full_context = {}
        for i, action_id in enumerate(self.actions):
            action_context = self.action_context_dict[action_id]
            full_context[action_id] = np.append(action_context, true_user_feature)

        return full_context

    def get_score_true(self, user_t):
        user_feature_index = self.user_id_to_index[user_t]

        user_feature = self.user_features_array[user_feature_index]
        user_bias = self.user_biases_array[user_feature_index]
        # True ratings used to compute the NDCG score.
        score_true = np.zeros((1, len(self.actions)))
        for i, action_id in enumerate(self.actions):
            action_context = self.action_context_dict[action_id]
            action_bias = self.action_bias_dict[action_id]

            user_item_tuple = (user_t, action_id)
            # If item is rated by user - use true rating as score.
            if user_item_tuple in self.user_item_to_rating:
                rating = self.user_item_to_rating[user_item_tuple]
            else:
                if self.implicit_feedback:
                    rating = 0
                else:
                    # Otherwise use rating estimated by matrix factorization.
                    # See https://surprise.readthedocs.io/en/stable/matrix_factorization.html#surprise.prediction_algorithms.matrix_factorization.SVD
                    rating = (
                        user_bias + action_bias + np.dot(action_context, user_feature)
                    )
                    rating = (
                        rating
                        if rating > self.ratings_range[0]
                        else self.ratings_range[0]
                    )
                    rating = (
                        rating
                        if rating < self.ratings_range[1]
                        else self.ratings_range[1]
                    )

            score_true[:, i] = rating

        return score_true

    def get_missing_vector(self, user_t):

        # Don't use this functionality
        return None

        if self.implicit_feedback:
            # In case of implicit feedback nothing is missing, because originally missing ratings are used as rating 0.
            return None

        missing_vector = np.zeros(len(self.actions))
        for i, action_id in enumerate(self.actions):
            user_item_tuple = (user_t, action_id)
            if user_item_tuple in self.user_item_to_rating:
                missing_vector[i] = 0
            else:
                missing_vector[i] = 1
        return missing_vector

    def generate_users(self, time_steps, tune=False):
        """Generate users and their corresponding data."""
        # Use last `time_steps` users in the user stream. We do this because later data is more dense, so we get all
        # users from a smaller time window this way.
        user_stream = self.tune_user_stream if tune else self.eval_user_stream

        assert (
            time_steps <= user_stream.shape[0]
        ), "Not enough users in user stream for given --times parameter"
        ind_start = user_stream.shape[0] - time_steps - 1
        ind_end = user_stream.shape[0] - 1
        if self.shift_back:
            ind_start -= 10000
            ind_end -= 10000

        if "timestamp" in user_stream.columns:
            print(
                f"First user in exp from {datetime.fromtimestamp(user_stream.timestamp.iloc[ind_start])}"
            )
            print(
                f"Last user in exp from {datetime.fromtimestamp(user_stream.timestamp.iloc[ind_end])}"
            )

        t = 0
        user_ind = ind_start
        while t < ind_end - ind_start:
            user_ind += 1
            user_t = user_stream.iloc[user_ind, 0]
            yield self.get_user_data(user_t)
            t += 1

    def generate_users_until_no_left(self, tune=False):
        """Generate users and their corresponding data not for fixed times, but unitl there are not users left"""
        user_stream = self.tune_user_stream if tune else self.eval_user_stream

        user_ind = 0
        while user_ind < len(user_stream):
            user_ind += 1
            user_t = user_stream.iloc[user_ind, 0]
            yield self.get_user_data(user_t)

    def get_user_data(self, user_id):
        try:
            watched_list_index = self.user_id_to_watched_list_index[user_id]
            reward_vector = self.reward_matrix[watched_list_index]
        except KeyError:
            reward_vector = np.zeros(self.reward_matrix.shape[1])

        # Create full context by concatenating user and item features.
        full_context = self.get_full_context(user_id)
        score_true = self.get_score_true(user_id)
        missing_vector = self.get_missing_vector(user_id)
        return full_context, reward_vector, score_true, missing_vector

    def generate_test_users(self):
        if self.test_user_ids is None:
            return []

        test_users_data = []
        for test_user_id in self.test_user_ids:
            test_users_data.append(self.get_user_data(test_user_id))
        return test_users_data

    def generate_experiment_reward_matrix(self, times, n_arms, tune):
        reward_vecs = np.zeros((times, n_arms))
        users = self.generate_users(times, tune=tune)
        for i, user_data in enumerate(users):
            context, reward_vector, score_true, missing_vector = user_data
            reward_vecs[i, :] = reward_vector
        return reward_vecs

    def sort_actions_based_on_experiment(self, times, n_arms, tune):
        """Sort actions list based on mean rewards in experiment.

        This is done for easy introduction of non-stationarity. This way first k arms are on average best k arms
        (!) for a given experiment.
        """
        print("Sorting actions based on experiment")
        exp_reward_matrix = self.generate_experiment_reward_matrix(times, n_arms, tune)
        exp_mean_rewards = np.mean(exp_reward_matrix, axis=0)
        self.actions = [x for _, x in sorted(zip(exp_mean_rewards, self.actions), key=lambda pair: pair[0], reverse=True)]

