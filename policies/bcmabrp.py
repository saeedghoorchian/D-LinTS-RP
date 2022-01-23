from collections import deque
import six
import numpy as np


class BCMABRP:
    def __init__(self, context_dimension, red_dim, reduct_matrix, delta=0.5, R=0.01, lambd=0.5, nu=0.5):
        super(BCMABRP, self).__init__()
        self.context_dimension = context_dimension
        self.red_dim = red_dim
        self.random_state = np.random.RandomState()
        self.lambd = lambd

        # # 0 < delta < 1
        # if not isinstance(delta, float):
        #     raise ValueError("delta should be float")
        # elif (delta < 0) or (delta >= 1):
        #     raise ValueError("delta should be in (0, 1]")
        # else:
        #     self.delta = delta

        # # R > 0
        # if not isinstance(R, float):
        #     raise ValueError("R should be float")
        # elif R <= 0:
        #     raise ValueError("R should be positive")
        # else:
        #     self.R = R  # pylint: disable=invalid-name

        # # 0 < epsilon < 1
        # if not isinstance(epsilon, float):
        #     raise ValueError("epsilon should be float")
        # elif (epsilon < 0) or (epsilon > 1):
        #     raise ValueError("epsilon should be in (0, 1)")
        # else:
        #     self.epsilon = epsilon

        # self.nu = R * np.sqrt(red_dim*np.log((2 + (2/lambd)) / delta))
        self.nu = nu  # 0.2 #1.5 #1

        self.model_param_memory = deque(maxlen=1)
        self.history_memory = deque(maxlen=1)

        self.reduction_matrix = reduct_matrix

        self.name = f"BCMABRP (nu={self.nu})"

    def update_history(self, hst):  # (context, recommendatin_id)
        self.history_memory.append(hst)
        # return self.history_memory

    def update_model_param(self, param):  # (B, f, inv_B)
        self.model_param_memory.append(param)

    def initialization(self):
        B = self.lambd * np.identity(self.red_dim)
        # psi_hat = np.zeros((self.red_dim, 1))
        f = np.zeros((self.red_dim, 1))
        inv_B = np.linalg.inv(B)  # .astype(np.float32)
        # print(self.model_param_memory)
        self.update_model_param((B, f, inv_B))
        # print(self.model_param_memory)

    def get_score(self, context, trial):
        action_ids = list(six.viewkeys(context))
        context_array = np.asarray([context[action_id] for action_id in action_ids])
        context_array = context_array.dot(self.reduction_matrix)

        B = self.model_param_memory[0][0]
        f = self.model_param_memory[0][1]
        inv_B = self.model_param_memory[0][2]
        # psi_hat = np.matmul(np.linalg.inv(B), f)
        B = B.astype(np.float32)
        psi_hat = (inv_B).dot(f).astype(np.float32)  # (np.linalg.inv(B)).dot(f).astype(np.float32)
        # psi_hat = psi_hat.astype(np.float32)
        # psi_tilde = self.random_state.multivariate_normal(psi_hat.flat, self.nu**2 * np.linalg.inv(B)) #[..., np.newaxis]
        psi_tilde = self.random_state.multivariate_normal(psi_hat.flat, self.nu ** 2 * inv_B)  # [..., np.newaxis]
        psi_tilde = np.reshape(psi_tilde, (-1, 1))
        estimated_reward_array = context_array.dot(psi_hat)
        score_array = context_array.dot(psi_tilde)

        estimated_reward_dict = {}
        uncertainty_dict = {}
        score_dict = {}
        for action_id, estimated_reward, score in zip(action_ids, estimated_reward_array, score_array):
            estimated_reward_dict[action_id] = float(estimated_reward)
            score_dict[action_id] = float(score)
            uncertainty_dict[action_id] = float(score - estimated_reward)
        return estimated_reward_dict, uncertainty_dict, score_dict  # , context_array

    def get_action(self, context, trial):
        # if not isinstance(context, dict):
        #     raise ValueError( "LinThompSamp requires context dict for all actions!")

        estimated_reward, uncertainty, score = self.get_score(context, trial)
        recommendation_id = max(score, key=score.get)
        self.update_history((context, recommendation_id))
        return recommendation_id

    # def reward(self, history_m, rewards):
    def reward(self, reward_t):
        # context = history_m[0][0]
        # recommendation_id = history_m[0][1]
        context = self.history_memory[0][0]
        recommendation_id = self.history_memory[0][1]
        B = self.model_param_memory[0][0]
        f = self.model_param_memory[0][1]
        # inv_B = self.model_param_memory[0][2]

        # for action_id, reward in six.viewitems(rewards):
        context_t = context[recommendation_id].dot(self.reduction_matrix)
        context_t = np.reshape(context_t, (-1, 1))
        B = B + context_t.dot(context_t.T)
        B = B.astype(np.float32)

        f = f + reward_t * context_t
        # psi_hat = np.linalg.inv(B).dot(f)
        inv_B = np.linalg.inv(B)  # .astype(np.float32)
        # print(self.model_param_memory)
        self.update_model_param((B, f, inv_B))
        # print(self.model_param_memory)
        # print("#############################################")
