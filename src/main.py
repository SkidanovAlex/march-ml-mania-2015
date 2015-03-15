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
    X, y, mean, std = get_training_data(2011)
    net = train_net(X, y)
    produce_output(net, mean, std)
