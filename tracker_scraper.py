import asyncio
import subprocess
import os
import json
import motor.motor_asyncio
from beanie import init_beanie
from model import TrackerDailyMMR, Score, Event

mmr_url = 'https://api.tracker.gg/api/v1/rocket-league/player-history/mmr/5751283'
stats_url = 'https://api.tracker.gg/api/v2/rocket-league/standard/profile/steam/GoshDarnedHero'
playlist_avg_url = 'https://api.tracker.gg/api/v2/rocket-league/standard/profile/steam/GoshDarnedHero/segments/playlistAverage'
session_url = 'https://api.tracker.gg/api/v2/rocket-league/standard/profile/steam/GoshDarnedHero/sessions'


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    return stdout


async def do_one():
    record = {
        'rating': 729,
        'tier': 'Platinum II',
        'division': 'Division II',
        'tierId': 11,
        'divisionId': 1,
        'collectDate': '2021-10-24T00:00:00+00:00'
    }
    record_to_insert = TrackerDailyMMR(**record)
    await record_to_insert.save()


async def get_mmr_history():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv('MONGO_URI')
    )
    document_models = [
        TrackerDailyMMR, Score
    ]
    await init_beanie(database=client.rocket_league, document_models=document_models)
    cmd = f'/usr/bin/curl -A Mozilla/5.0 {mmr_url}'
    response = await run(cmd)
    mmr_history = json.loads(response)
    daily_history = mmr_history['data']['11']
    for day in daily_history:
        print(day)
        day_record = TrackerDailyMMR(**day)
        await day_record.save()


async def getEvent():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv('MONGO_URI')
    )
    document_models = [
        Event,
        Score,
    ]
    await init_beanie(database=client.rocket_league, document_models=document_models)

    current_scores = await Score.find(
        Score.data.name == 'GoshDarnedHero'
    ).sort("-timestamp").limit(1).to_list()
    current_score = current_scores[0]
    print(current_score.data.score)

if __name__ == "__main__":

    # asyncio.run(init_db())
    # asyncio.run(get_mmr_history())
    # asyncio.run(get_mmr_history())
    asyncio.run(getEvent())
