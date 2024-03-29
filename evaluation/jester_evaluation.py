import numpy as np


def evaluate_policy_on_jester(policy, times, actions, action_features, user_stream, user_features, reward_list):
    seq_reward = np.zeros(shape=(times, 1))

    action_context_dict = {}
    for action_id in actions:  # joke_id :)
        action_context_dict[action_id] = np.array(action_features[action_features['item_id'] == action_id])[0][1:]

    rew = 0
    t = 0
    while t < times:  # for t in range(times):

        user_t = user_stream[t]

        feature = np.array(user_features[user_features["user_id"] == user_t])[0][1:]
        full_context = {}
        for action_id in actions:  # movie_id :)
            full_context[action_id] = np.append(action_context_dict[action_id], feature)  # feature

        #                 print(full_context[action_id].shape)

        action_t = policy.get_action(full_context, t)

        watched_list = np.array(reward_list[reward_list["user_id"] == user_t]["item_id"])
        # print("user_t: " + str(user_t))
        # print("Data_t: " + str(top_jokes[top_jokes["user_id"] == user_t]))
        # print("action_t: " + str(action_t))
        # print("watched_list: " + str(watched_list))
        # watched_list = watched_list.astype(np.int)
        # print("watched_list integer: " + str(watched_list))
        # print("T/NT: " + str(action_t not in watched_list))

        if action_t not in watched_list:
            policy.reward(0.0)
            if t == 0:
                seq_reward[t] = 0.0
            if t > 0:
                seq_reward[t] = seq_reward[t - 1]

        else:
            policy.reward(1.0)
            if t == 0:
                seq_reward[t] = 1.0
            else:
                seq_reward[t] = seq_reward[t - 1] + 1.0

        if t % 1000 == 0:
            print(t)

        t = t + 1

    return seq_reward
