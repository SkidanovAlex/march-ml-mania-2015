from model import *
import pprint

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    #populate_all_teams_players_stats(2011)
    #populate_all_teams_players_stats(2012)
    #populate_all_teams_players_stats(2013)
    #populate_all_teams_players_stats(2014)
    #opulate_all_teams_players_stats(2015)
    #number_of_players_per_team()
    #print len(load_game_results())
    #pp.pprint(load_players_stats())
    nets = {}
    for season in range(2011, 2016):
        X, y, mean, std = get_training_data(season)
        net = train_net(X, y)
        nets[season] = net
    produce_output(nets, mean, std)
