from nolearn import lasagne
import csv

def load_game_results(): # return [(year, wteam, lteam, wscore, lscore)...]
    game_res = []
    for fname in ["../data/regular_season_compact_results.csv", "../data/tourney_compact_results.csv"]:
        with open(fname) as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                if int(row[0]) >= 2011:
                    game_res.append((int(row[0]), int(row[2]), int(row[4]), int(row[3]), int(row[5])))
    return game_res