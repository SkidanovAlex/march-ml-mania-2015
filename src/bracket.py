from model import get_features_vector
from model import load_players_stats
from model import regression
from collect import get_kaggle_teams
import csv
import numpy as np

def predict_bracket_naive(net, mean, std):
    seeds = [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]
    seeds = [x - 1 for x in seeds]
    inv_seeds = [0 for i in range(16)]
    for i,s in enumerate(seeds):
        inv_seeds[s] = i

    player_stats = load_players_stats()
    team_names = {}
    for k, v in get_kaggle_teams():
        team_names[int(k)] = v

    teams = [0 for x in range(64)]
    bracket = []
    with open("../data/tourney_seeds_2015.csv") as f:
        reader = csv.reader(f)
        next(reader)
        ord = 0
        qua = 0
        for row in reader:
            if row[1].endswith('a'):
                continue
            teams[qua + inv_seeds[ord]] = int(row[2])
            ord += 1
            if ord % 16 == 0:
                qua += 16
                ord = 0

    bracket.append(teams)
    while len(teams) > 1:
        new_teams = []
        #print "--", len(teams)
        for i in range(0, len(teams), 2):
            #print i
            t1 = teams[i]
            t2 = teams[i + 1]
            features = get_features_vector(2016, t1, t2, player_stats)
            if features is None:
                assert False, "%s %s" % (t1, t2)
            features = np.array([features])
            features = (features - mean) / std
            features = features.astype(np.float32)
            predicted = net.predict_proba(features)
            if predicted > 0.5:
                new_teams.append(t1)
            else:
                new_teams.append(t2)
        teams = new_teams
        bracket.append(new_teams)

    print "<table>"
    for i in range(64):
        print "<tr>"
        for j in range(7):
            if i % (1 << j) == 0:
                print "<td style='border:1px solid black' rowspan=%s>%s</td>" % (1 << j, team_names[bracket[j][i >> j]])
        print "</tr>"
    print "</table>"


def rec(player_stats, net, mean, std, inv_seeds, bracket, x, y, team, memo, fill):
    if x == 0:
        return (0, 1)

    if (x, y, team) in memo and not fill:
        return memo[(x, y, team)]

    l = team & ~((1 << x) - 1)
    r = l + (1 << x)
    m = l + (1 << (x - 1))
    p = 0
    #print l, r, m
    if team < m:
        best = -1
        bestScore = -1
        s1, p1 = rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2, team, memo, False)
        for i in range(m, r):
            t1 = team
            t2 = i
            features = get_features_vector(2016, bracket[0][t1], bracket[0][t2], player_stats)
            #print t1, t2
            features = np.array([features])
            features = (features - mean) / std
            features = features.astype(np.float32)
            s2, p2 = rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2 + 1, t2, memo, False)
            p += net.predict_proba(features)[0][0 if regression else 1] * p1 * p2
            if s2 > bestScore:
                bestScore = s2
                best = i
        if fill:
            rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2, team, memo, True)
            rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2 + 1, best, memo, True)
            bracket[x][y] = bracket[0][team]
    else:
        best = -1
        bestScore = -1
        s1, p1 = rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2 + 1, team, memo, False)
        for i in range(l, m):
            t1 = team
            t2 = i
            features = get_features_vector(2016, bracket[0][t1], bracket[0][t2], player_stats)
            #print t1, t2
            features = np.array([features])
            features = (features - mean) / std
            features = features.astype(np.float32)
            s2, p2 = rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2, t2, memo, False)
            p += net.predict_proba(features)[0][0 if regression else 1] * p1 * p2
            if s2 > bestScore:
                bestScore = s2
                best = i
        if fill:
            rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2 + 1, team, memo, True)
            rec(player_stats, net, mean, std, inv_seeds, bracket, x - 1, y * 2, best, memo, True)
            bracket[x][y] = bracket[0][team]

    score = s1 + bestScore + p * (1 << x)
    assert best != -1
    #print p
    if p > 1: p = 1
    memo[(x, y, team)] = (score, p)
    return (score, p)



def predict_bracket_smart(net, mean, std):
    seeds = [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]
    seeds = [x - 1 for x in seeds]
    inv_seeds = [0 for i in range(16)]
    for i,s in enumerate(seeds):
        inv_seeds[s] = i

    player_stats = load_players_stats()
    team_names = {}
    for k, v in get_kaggle_teams():
        team_names[int(k)] = v

    teams = [0 for x in range(64)]
    bracket = []
    with open("../data/TourneySeeds.csv") as f:
        reader = csv.reader(f)
        next(reader)
        ord = 0
        qua = 0
        for row in reader:
            if row[1].endswith('b'):
                continue
            if int(row[0]) != 2016:
                continue
            teams[qua + inv_seeds[ord]] = int(row[2])
            ord += 1
            if ord % 16 == 0:
                qua += 16
                ord = 0

    bracket.append(teams)
    for i in range(6):
        bracket.append([0 for x in range(len(bracket[-1])/2)])

    memo = {}
    rec(player_stats, net, mean, std, inv_seeds, bracket, 6, 0, 32, memo, True)

    print "<table>"
    for i in range(64):
        print "<tr>"
        for j in range(7):
            if i % (1 << j) == 0:
                print "<td style='border:1px solid black' rowspan=%s>%s</td>" % (1 << j, team_names[bracket[j][i >> j]])
        print "</tr>"
    print "</table>"