import requests
import sys
import time
import json
import collections
import argparse

USER_URL = "https://www.speedrun.com/api/v1/users/{}"
RUNS_URL = "https://www.speedrun.com/api/v1/runs?user={}&max=200&offset={}"
GAME_URL = "https://www.speedrun.com/api/v1/games/{}?embed=levels,categories,platforms,regions,variables"

MAX_REQUESTS = 100

req_count = 0
q = collections.deque(list(), MAX_REQUESTS)
        
def check_request():
    if len(q) == MAX_REQUESTS:
        delta = (int(time.time()) - q[0])
        if delta < 60:
            print("Waiting {} seconds for requests...".format(60-delta))
            time.sleep(60-delta)
    q.append(int(time.time()))

def do_request(url):
    check_request()

    r = requests.get(url)

    if r.status_code >= 400:
        # print the body message as an error
        print("Error: " + r.reason)
        return

    return r

def srdc_backup(username, image):
    udata = do_request(USER_URL.format(username)).json()['data']

    # IF DOWNLOAD ICONS
    if image:
        print("Downloading images...")
        try:
            ico = requests.get(udata['assets']['icon']['uri'])
            with open("{}_ico.png".format(udata['id']),"wb") as f:
                f.write(ico.content)
                print("Wrote {}_ico.png".format(udata['id']))
        except Exception as e:
            print(e)
            print("No icon being written")
        try:
            img = requests.get(udata['assets']['image']['uri'])
            with open("{}_img.png".format(udata['id']),"wb") as f:
                f.write(img.content)
                print("Wrote {}_img.png".format(udata['id']))
        except Exception as e:
            print(e)
            print("No image being written")

    print("Grabbing runs...")
    offset = 0
    runs = list()
    while True:
        resp = do_request(RUNS_URL.format(udata['id'], offset)).json()
        runs += resp['data']
        
        if resp['pagination']['size'] < 200:
            break

        offset += 200
    print("Run count: " + str(len(runs)))
    print("Enumerating games...")
    game_names = list()
    for run in runs:
        if run['game'] not in game_names:
            game_names.append(run['game'])
    game_count = len(game_names)
    print("Game count: " + str(game_count))
    print("Approximate time to download: {} min".format("<1" if (game_count < 100) else game_count//100))
    games = list()
    for name in game_names:
        game_data = do_request(GAME_URL.format(name)).json()['data']
        games.append(game_data)
    

    print("Removing irrelevant information...")
    #before packaging the stuff up, it's worth removing all the irrelevant info
    #so we pop from each dict the unneeded stuff
    udata.pop('assets')
    udata.pop('weblink')
    udata.pop('links')

    for run in runs:
        run.pop('weblink')
        run.pop('links')
        for player in run['players']:
            player.pop('uri')

    for game in games:
        game.pop('assets')
        game.pop('weblink')
        game.pop('links')
        for category in game['categories']['data']:
            category.pop('links')
            category.pop('weblink')
        for level in game['levels']['data']:
            level.pop('links')
            level.pop('weblink')
        for platform in game['platforms']['data']:
            platform.pop('links')
        for region in game['regions']['data']:
            region.pop('links')
        for variable in game['variables']['data']:
            variable.pop('links')

    backup_file = "{}_backup.json".format(udata['id'])
    print("Packaging and writing JSON to {}...".format(backup_file))
    final_json = dict()
    final_json['user'] = udata
    final_json['games'] = games
    final_json['runs'] = runs
    with open(backup_file,"w") as f:
        f.write(json.dumps(final_json))
    print("Done.")

def main():
    parser = argparse.ArgumentParser(description='Backup SRDC to JSON.')
    parser.add_argument('username',
                    help='Username to back up data for.')
    parser.add_argument('-i', '--image', action="store_true",
                    help='Download icon and donator image.')
    args = parser.parse_args()
    srdc_backup(args.username, args.image)

if __name__ == '__main__':
    main()
