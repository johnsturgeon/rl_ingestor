import json
import time

import requests
base_url='http://127.0.0.1:8822/rl_event/'


def replay_game():
    with open('one_match.json') as json_file:
        game_data = json.load(json_file)
    for game_event in game_data:
        url = base_url + game_event['event_name']
        post_data = game_event['post_data']
        requests.post(url, json=post_data)
        time.sleep(.1)
        print(game_event)

if __name__ == '__main__':
    replay_game()