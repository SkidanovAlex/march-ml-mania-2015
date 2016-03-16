from lasagne import layers
from custom_layers import NCAALayer, team_features
from lasagne import nonlinearities
from lasagne.updates import nesterov_momentum
from nolearn.lasagne import NeuralNet
from collect import get_kaggle_teams
import numpy as np
from sklearn import preprocessing
from sklearn.utils import shuffle
import theano
import csv
import os

regression = False

features_per_player = 110
players_per_team = 5
num_features = players_per_team * features_per_player + team_features

coach_features = 6

def float32(k):
    return np.cast['float32'](k)


def load_game_results(): # return [(year, wteam, lteam, wscore, lscore)...]
    game_res = []
    #for fname in ["../data/regular_season_compact_results.csv", "../data/tourney_compact_results.csv", "../data/regular_season_compact_results_2015_Sunday.csv"]:
    for fname in ["../data/RegularSeasonCompactResults.csv", "../data/TourneyCompactResults.csv"]:
        with open(fname) as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                if int(row[0]) >= 2011:
                    game_res.append((int(row[0]), int(row[2]), int(row[4]), int(row[3]), int(row[5])))
    return game_res


def load_players_stats(): # returns {('team_id', 'season'): [features...]}
    ret = {}
    offsets = [1, 1 + 26 - 4, 1 + 26 + 24 - 4 * 2, 1 + 26 + 24 + 24 - 4 * 3, 1 + 26 + 24 + 24 + 27 - 4 * 4, features_per_player]
    id_name = get_kaggle_teams()
    for season in range(2011, 2017):
        for team_id, name in id_name:
            features = [0 for _ in range(num_features)]
            fname = '../data/generated/team_players/%s_%s_data.txt' % (team_id, season)
            if not os.path.exists(fname):
                continue
            player_gpl = []
            with open(fname) as f:
                for line in f.readlines():
                    tokens = line.split(',')
                    pid = int(tokens[0])
                    sid = int(tokens[1])
                    gpl = int(tokens[2])

                    if sid == 0:
                        player_gpl.append((pid, gpl))

            player_gpl = sorted(player_gpl, key=lambda x: x[1], reverse=True)
            if len(player_gpl) > players_per_team:
                player_gpl = player_gpl[:players_per_team]
            pid_to_ord = {}
            for i, tup in enumerate(player_gpl):
                pid_to_ord[tup[0]] = i

            with open(fname) as f:
                for line in f.readlines():
                    tokens = line.split(',')
                    pid = int(tokens[0])
                    sid = int(tokens[1])
                    gpl = int(tokens[2])

                    if pid not in pid_to_ord:
                        continue

                    player_ordinal = pid_to_ord[pid]

                    if sid == 0:
                        features[features_per_player * player_ordinal] = gpl
                        if len(tokens) == 27:
                            tokens = tokens[:-2] # drop last two columns, as they were not collected for 2016 (also one but last is always empty)

                    assert len(tokens[3:]) == offsets[sid + 1] - offsets[sid], "%s != %s for %s (%s)" % (len(tokens[3:]), offsets[sid + 1] - offsets[sid], sid, fname)
                    for i, token in enumerate(tokens[3:]):
                        pos = offsets[sid] + features_per_player * player_ordinal + i
                        token = token.strip()
                        if token == "":
                            features[pos] = 0
                        else:
                            try:
                                features[pos] = float(token)
                            except ValueError as e:
                                print '[', token, ']'
            fname = '../data/generated/team_players/%s_%s_coach.txt' % (team_id, season)
            with open(fname, 'r') as f:
                total_lines = 0
                for line in f.readlines():
                    total_lines += 1
                    tokens = [(float(x) if len(x) > 0 else 0.0) for x in line.split(',')[:coach_features]]
                    for i in range(coach_features):
                        features[features_per_player * players_per_team + i] += tokens[i]
                if total_lines == 0:
                    total_lines = 1
                for i in range(coach_features):
                    features[features_per_player * players_per_team + i] /= float(total_lines)
            fname = '../data/generated/team_players/%s_%s_team.txt' % (team_id, season)
            with open(fname, 'r') as f:
                for line in f.readlines():
                    tokens = [(float(x) if len(x) > 0 else 0.0) for x in line.split(',')[:team_features - coach_features]]
                    for i in range(team_features - coach_features):
                        features[features_per_player * players_per_team + coach_features + i] += tokens[i]
            ret[(int(team_id), season)] = features

    return ret


def score_diff_to_output(a, b):
    x = a - b
    return 1 if x > 0 else 0
    #if x < -20: x = -20
    #if x > 20: x = 20
    #return (x + 20) / 40.0


def get_features_vector(season, t1, t2, player_stats):
        if (t1, season) not in player_stats or (t2, season) not in player_stats:
            return None
        return player_stats[(t1, season)] + player_stats[(t2, season)]


def get_training_data(season):
    player_stats = load_players_stats()
    skipped = 0
    total = 0
    X = []
    y = []
    for game in load_game_results():
        if game[0] == season:
            continue
        total += 1
        xx = get_features_vector(game[0], game[1], game[2], player_stats)
        if xx is None:
            skipped += 1
            continue
        X.append(xx)
        if regression:
            y.append((score_diff_to_output(game[3], game[4]),))
        else:
            y.append((score_diff_to_output(game[3], game[4])))

        xx = get_features_vector(game[0], game[2], game[1], player_stats)
        if xx is None:
            assert False
        X.append(xx)
        if regression:
            y.append((score_diff_to_output(game[4], game[3]),))
        else:
            y.append((score_diff_to_output(game[4], game[3])))

    xMean = np.mean(X, axis=0)
    xStd = np.std(X, axis=0)
    xStd[xStd == 0] = 1
    X = np.array(X)
    y = np.array(y, np.int32)
    X = preprocessing.scale(X)
    X, y = shuffle(X, y, random_state=42)
    assert skipped * 10 < total

    X = X.astype(np.float32)
    if regression:
        y = y.astype(np.float32)
    return X, y, xMean, xStd


def train_net(X, y):
    print X.shape, y.shape
    net2 = NeuralNet(
    layers=[
        ('input', layers.InputLayer),
        ('ncaa', NCAALayer),
        ('dropout1', layers.DropoutLayer),
        ('hidden', layers.DenseLayer),
        ('dropout2', layers.DropoutLayer),
        ('output', layers.DenseLayer),
        ],
    input_shape = (None, num_features * 2),
    ncaa_num_units = 128,
    dropout1_p=0.2,
    hidden_num_units=128,
    dropout2_p=0.3,
    output_nonlinearity=nonlinearities.sigmoid if regression else nonlinearities.softmax,
    output_num_units=1 if regression else 2,

    update=nesterov_momentum,
    update_learning_rate=0.01,
    update_momentum=theano.shared(float32(0.9)),

    regression=regression,  # flag to indicate we're dealing with regression problem
    max_epochs=50,  # we want to train this many epochs
    verbose=1,
    )

    net2.fit(X, y)
    return net2


def produce_output(nets, mean, std):
    player_stats = load_players_stats()
    total = 0
    skipped = 0
    with open('../data/SampleSubmission.csv') as f:
        with open('../data/submission_2016.csv', 'w') as fw:
            lines = f.readlines()
            fw.write("%s" % lines[0])
            for line in lines[1:]:
                total += 1
                tokens = line.split(',')
                tokens = [int(x) for x in tokens[0].split('_')]
                season = tokens[0]
                t1 = tokens[1]
                t2 = tokens[2]
                assert int(t1) < int(t2)
                features = get_features_vector(season, t1, t2, player_stats)
                if features is None:
                    fw.write("%s" % line)
                    skipped += 1
                    continue
                features = np.array([features])
                features = (features - mean) / std
                features = features.astype(np.float32)
                predicted = nets[season].predict_proba(features)
                fw.write("%s,%s\n" % (line.split(',')[0], predicted[0][0] if regression else predicted[0][1]))

    print total, skipped
