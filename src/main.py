from collect import *
import pprint

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    try:
        populate_all_teams_players_stats(2012)
    except:
        print "FAILED 2012"
        raise
    try:
        populate_all_teams_players_stats(2013)
    except:
        print "FAILED 2013"
    try:
        populate_all_teams_players_stats(2014)
    except:
        print "FAILED 2014"
