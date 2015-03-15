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


def parse_player_table(soup, id, expected_len, season):
    ret = ''
    div = soup.find(id=id).tbody
    found = False
    for tr in div.find_all('tr'):
        data = [td.text for td in tr.find_all('td')]
        assert len(data) == expected_len, "%s != %s = len(%s)" % (expected_len, len(data), data)
        if data[0] == "%s-%s" % (season - 1, season % 100):
            ret = ','.join(data[3:]) + '\n'
            assert not found
            found = True
    assert found
    return ret


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

    player_ordinal = 0
    with open(fname) as f:
        with open(fout, 'w') as fw:
            for line in f.readlines():
                line = line.strip()
                if line != "":
                    print line
                    soup = get_page_soup(line, None)
                    fw.write("%s,%s,%s" % (player_ordinal, 0, parse_player_table(soup, 'players_totals', 26, season)))
                    fw.write("%s,%s,%s" % (player_ordinal, 1, parse_player_table(soup, 'players_per_game', 24, season)))
                    fw.write("%s,%s,%s" % (player_ordinal, 2, parse_player_table(soup, 'players_per_min', 24, season)))
                    fw.write("%s,%s,%s" % (player_ordinal, 3, parse_player_table(soup, 'players_per_poss', 27, season)))
                    fw.write("%s,%s,%s" % (player_ordinal, 4, parse_player_table(soup, 'players_advanced', 28, season)))
                    player_ordinal += 1


def populate_all_teams_players_stats(season):
    id_name = get_kaggle_teams()

    for id, name in id_name:
        print "Populating for %s (%s)" % (name, season)
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
