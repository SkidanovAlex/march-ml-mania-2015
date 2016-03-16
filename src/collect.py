from utils import str_dist
from hardcoded import kaggle_to_collected
from bs4 import BeautifulSoup
import requests
import csv
import os


def get_page_content(url):
    r = requests.get(url)
    assert r.status_code == 200, r.status_code
    return r.text


def get_page_soup(url, file): # if file exists, open file, else the url
    if file is not None and os.path.exists(file):
        with open(file) as f:
            content = f.read()
    else:
        content = get_page_content(url)
        content = content.replace(u"\ufffd", "").replace(u"\xa0", "") # fight some unicode errors I don't want to deal with
        if file is not None:
            with open(file, 'w') as f:
                f.write(content)
    return BeautifulSoup(content)


def normalize_url(url):
    url_prefix = "http://www.sports-reference.com"
    if url.startswith(url_prefix):
        return url
    return url_prefix + url


def get_teams(): # returns [{url:, name:}]
    s = get_page_soup("http://www.sports-reference.com/cbb/schools/", "../data/collected/teams.html")
    ret = []
    prefix = "/cbb/schools/"
    base_url = "http://www.sports-reference.com"
    for link in s.find_all('a'):
        href = link.get('href')
        if href.startswith(base_url):
            href = href[len(base_url):]
        if href is not None and href.startswith(prefix) and href != prefix:
            ret.append({'name': link.text.strip(), 'url': href})
    return ret


def get_teams_stats(): # returns {'name':[stats]}
    ret = {}
    with open('../data/collected/teams.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == 'Rk':
                continue
            ret[row[1]] = row
    return ret


def get_teams_for_seasons(first_season): # returns [{url:, name:}]
    ret = []
    all_teams = get_teams()
    team_stats = get_teams_stats()
    for team in all_teams:
        if team['name'] not in team_stats:
            continue # different spellings
        if int(team_stats[team['name']][3]) >= first_season:
            ret.append(team)
    return ret


def get_kaggle_teams(): # returns [(id, name)]
    ret = []
    with open('../data/teams.csv') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for row in reader:
            ret.append((row[0], row[1]))
    return ret


def match_kaggle_and_collected_teams(): # returns {kaggle name: collected name}
    # this is just an approximation. manually corrected result is in hardcoded.py
    ret = {}
    kaggle = [x[1] for x in get_kaggle_teams()]
    collected = [x['name'] for x in get_teams_for_seasons(2011)]

    for k in kaggle:
        if k.startswith('WI ') or k.startswith('UT '):
            k = k[3:] # drop the WI
        if k.startswith('W '):
            k = 'Western ' + k[2:]
        best = 0
        bestScore = str_dist(k, collected[0])
        for c in collected[1:]:
            score = str_dist(k, c)
            if score > bestScore:
                bestScore = score
                best = c
        ret[k] = best
    return ret


def populate_team_players(season):
    # for each team, populate player names into a file ../data/generated/team_players/<teamid>_<season>.txt, one url per line
    # teams is {'kaggle' : "collected"}, as stored in hardcoded.py
    id_name = get_kaggle_teams()
    name_to_url = {}
    for entry in get_teams():
        name_to_url[entry['name']] = entry['url']

    for id, name in id_name:
        remote_name = kaggle_to_collected[name]
        if remote_name is None:
            continue

        fname = '../data/generated/team_players/%s_%s.txt' % (id, season)
        cached_page = '../data/generated/team_players/%s_%s.html' % (id, season)
        url = normalize_url('%s/%s.html' % (name_to_url[remote_name], season))
        print remote_name, url
        if os.path.exists(fname):
            print "Skipping %s, as `%s` exists" % (remote_name, fname)
            continue

        soup = get_page_soup(url, cached_page)
        roster = soup.find(id='roster')
        if roster is None:
            continue

        with open(fname, 'w') as fw:
            prefix = "http://www.sports-reference.com/cbb/players/"
            for link in roster.find_all('a'):
                href = normalize_url(link.get('href'))
                if href.startswith(prefix) and href != prefix:
                    fw.write("%s\n" % href.replace('\xa0', '-'))


def parse_player_table(soup, id, expected_len, season_or_url, ok_to_not_find=None):
    ret = ''
    div = soup.find(id=id)
    if div is None:
        assert season_or_url == 2016
        return ','.join(['0' for x in range(expected_len - 3)]) + '\n'
    div = div.tbody
    found = False
    saw_good_len = False
    for tr in div.find_all('tr'):
        data = [td.text for td in tr.find_all('td')]
        if type(season_or_url) != int:
            data = ['0'] + data # main page has one less column in front and misses last two for the totals
            if expected_len == 28 and len(data) == 26:
                data = data + ['', '0']

        if len(data) == 30 and expected_len == 28:
            data = data[:28] # drop the awards
        assert len(data) == expected_len or (len(data) == 0 and saw_good_len), "%s != %s = len(%s)" % (expected_len, len(data), data)
        if len(data) == 0:
            continue
        saw_good_len = True
        if season_or_url in [normalize_url(a.get('href')) for a in tr.find_all('a')] or (type(season_or_url) == int and "%s-%s" % (season_or_url - 1, season_or_url % 100) in data[0:2]):
            ret = ','.join(data[3:]) + '\n'
            assert not found
            found = True
    if not found:
        assert (ok_to_not_find is None and (type(season_or_url) != int or season_or_url == 2016)) or ok_to_not_find, season_or_url
        return ','.join(['0' for x in range(expected_len - 3)]) + '\n'
    return ret


def populate_team_stats_for_season(season):
    # for each team, populate player names into a file ../data/generated/team_players/<teamid>_<season>.txt, one url per line
    # teams is {'kaggle' : "collected"}, as stored in hardcoded.py
    id_name = get_kaggle_teams()
    name_to_url = {}
    for entry in get_teams():
        name_to_url[entry['name']] = entry['url']

    for id, name in id_name:
        remote_name = kaggle_to_collected[name]
        if remote_name is None:
            continue

        url = normalize_url(name_to_url[remote_name])
        cached_page = '../data/generated/team_players/%s_team.html' % id
        fname = '../data/generated/team_players/%s_%s_team.txt' % (id, season)

        if not os.path.exists(fname) or True:
            print url, season
            soup = get_page_soup(url, cached_page)
            with open(fname, 'w') as fw:
                fw.write(parse_player_table(soup, [x for x in url.split('/') if len(x) > 0][-1], 15, season, ok_to_not_find=True))

        else:
            print "Skipping populating team stats for %s, as the file already exists" % remote_name


def populate_coaches_stats_for_season(season):
    # for each team, populate player names into a file ../data/generated/team_players/<teamid>_<season>.txt, one url per line
    # teams is {'kaggle' : "collected"}, as stored in hardcoded.py
    id_name = get_kaggle_teams()
    name_to_url = {}
    for entry in get_teams():
        name_to_url[entry['name']] = entry['url']

    for id, name in id_name:
        remote_name = kaggle_to_collected[name]
        if remote_name is None:
            continue

        fname = '../data/generated/team_players/%s_%s_coach.txt' % (id, season)
        cached_page = '../data/generated/team_players/%s_%s.html' % (id, season)
        cached_coach_page = '../data/generated/team_players/%s_%s_coach.html' % (id, season)
        url = normalize_url('%s/%s.html' % (name_to_url[remote_name], season))
        print remote_name, url
        #if os.path.exists(fname):
        #    print "Skipping %s, as `%s` exists" % (remote_name, fname)
        #    continue

        if not os.path.exists(cached_coach_page):
            soup = get_page_soup(url, cached_page)
            info_box = soup.find(id='info_box')
            if info_box is None:
                print "Skipping %s, info_box not present" % remote_name
                continue

            found = False
            with open(fname, 'w') as fw:
                prefix = "http://www.sports-reference.com/cbb/coaches/"
                for link in info_box.find_all('a'):
                    href = normalize_url(link.get('href'))
                    if href.startswith(prefix) and href != prefix:
                        soup = get_page_soup(href, cached_coach_page)
                        fw.write(parse_player_table(soup, 'stats', 13, season))
                        found = True
            assert found


def num_lines(fname):
    with open(fname) as f:
        return len(f.readlines())


def populate_players_stats(team_id, season):
    fname = '../data/generated/team_players/%s_%s.txt' % (team_id, season)
    fout = '../data/generated/team_players/%s_%s_data.txt' % (team_id, season)
    if not os.path.exists(fname):
        #print "Skipping %s %s, as the corresponding input file doesn't exist" % (team_id, season)
        return

    if os.path.exists(fout) and os.path.getsize(fout) > 0:
        if num_lines(fout) != 5 * num_lines(fname):
            pass
        else:
            #print "Skipping %s %s, as the corresponding output file already exists" % (team_id, season)
            return



    id_name = get_kaggle_teams()
    for id, name in id_name:
        if id == team_id:
            remote_name = kaggle_to_collected[name]
            break
    else:
        assert False, team_id

    name_to_url = {}
    for entry in get_teams():
        name_to_url[entry['name']] = entry['url']

    if remote_name is None:
        return

    cached_page = '../data/generated/team_players/%s_%s.html' % (team_id, season)
    url = normalize_url('%s/%s.html' % (name_to_url[remote_name], season))

    print url
    soup = get_page_soup(url, cached_page)



    player_ordinal = 0
    with open(fname) as f:
        with open(fout, 'w') as fw:
            for line in f.readlines():
                line = line.strip()
                if line != "":
                    # the soup fetched below opens the player's page. this was the old way of collecting stats. now
                    #    they are collected from the team page. if the old way becomes preferred again (e.g. because
                    #    player page has more features), `all_*` need to be changed to `player_*` and last argument
                    #    needs to be changed to `season` instead of `line`.
                    #print line
                    #soup = get_page_soup(line, None)
                    fw.write("%s,%s,%s" % (player_ordinal, 0, parse_player_table(soup, 'all_totals', 28, line)))
                    fw.write("%s,%s,%s" % (player_ordinal, 1, parse_player_table(soup, 'all_per_game', 24, line)))
                    fw.write("%s,%s,%s" % (player_ordinal, 2, parse_player_table(soup, 'all_per_min', 24, line)))
                    fw.write("%s,%s,%s" % (player_ordinal, 3, parse_player_table(soup, 'all_per_poss', 27, line)))
                    fw.write("%s,%s,%s" % (player_ordinal, 4, parse_player_table(soup, 'all_advanced', 28, line)))
                    player_ordinal += 1


def populate_all_teams_players_stats(season):
    id_name = get_kaggle_teams()

    for id, name in id_name:
        print "Populating for #%s %s (%s)" % (id, name, season)
        populate_players_stats(id, season)


def number_of_players_per_team(): # helper to get min and max number of players per team
    id_name = get_kaggle_teams()
    mn = 100
    mx = 0
    for season in range(2011, 2016):
        for team_id, name in id_name:
            fname = '../data/generated/team_players/%s_%s_data.txt' % (team_id, season)
            if not os.path.exists(fname):
                continue
            with open(fname) as f:
                x = len(f.readlines())
                if x < mn: mn = x
                if x > mx: mx = x
    print mn / 5, mx / 5
