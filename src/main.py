import sys
from model import *
from collect import *
from bracket import predict_bracket_naive, predict_bracket_smart
import pprint

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    for season in [2011, 2012, 2013, 2014, 2015, 2016]:
        #populate_team_players(season)
        #populate_all_teams_players_stats(season)
        #populate_coaches_stats_for_season(season)
        #populate_team_stats_for_season(season)
        pass
    #number_of_players_per_team()
    #print len(load_game_results())
    #pp.pprint(load_players_stats())
    nets = {}
    X, y, mean, std = get_training_data(2016)
    print "HERE"
    net = train_net(X, y)
    nets[2016] = net
    produce_output(nets, mean, std)
    predict_bracket_smart(net, mean, std)
