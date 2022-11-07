import asyncio
import datetime
import arrow
import os
import json
import motor.motor_asyncio
from beanie import init_beanie
from model import TrackerDailyMMR, TrackerStats

mmr_url = 'https://api.tracker.gg/api/v1/rocket-league/player-history/mmr/5751283'
stats_url = 'https://api.tracker.gg/api/v2/rocket-league/standard/profile/steam/GoshDarnedHero'
playlist_avg_url = 'https://api.tracker.gg/api/v2/rocket-league/standard/profile/steam/GoshDarnedHero/segments/playlistAverage'
session_url = 'https://api.tracker.gg/api/v2/rocket-league/standard/profile/steam/GoshDarnedHero/sessions'

RANKED_DOUBLES_PLAYLIST = 11


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    return stdout


async def get_mmr_history():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv('MONGO_URI')
    )
    document_models = [
        TrackerDailyMMR,
        TrackerStats
    ]
    await init_beanie(database=client.rocket_league, document_models=document_models)
    cmd = f'/usr/bin/curl -A Mozilla/5.0 {mmr_url}?$RANDOM'
    response = await run(cmd)
    mmr_history = json.loads(response)
    daily_history = mmr_history['data']['11']
    for day in daily_history:
        collect_date = day['collectDate']
        record_exists = TrackerDailyMMR.find_one(TrackerDailyMMR.collectDate == collect_date)
        if not record_exists:
            day_record = TrackerDailyMMR(**day)
            await day_record.save()


def get_playlist_from_stats(stats, playlist_id) -> dict:
    for segment in stats['data']['segments']:
        if segment['type'] != 'playlist':
            continue
        if segment['attributes']['playlistId'] == playlist_id:
            return segment['stats']
    return {}


async def get_stats():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv('MONGO_URI')
    )
    document_models = [
        TrackerDailyMMR,
        TrackerStats
    ]
    await init_beanie(database=client.rocket_league, document_models=document_models)

    cmd = f'/usr/bin/curl -A Mozilla/5.0 {stats_url}'
    response = await run(cmd)
    stats = json.loads(response)
    playlist_stats = get_playlist_from_stats(stats, RANKED_DOUBLES_PLAYLIST)
    timestamp = arrow.utcnow().int_timestamp
    rating = playlist_stats['rating']['value']
    tier = playlist_stats['tier']['metadata']['name']
    division = playlist_stats['division']['metadata']['name']
    icon_url = playlist_stats['tier']['metadata']['iconUrl']
    prev_records = await TrackerStats.find_all().sort('-timestamp').limit(1).to_list()
    should_save = False
    if not prev_records:
        should_save = True
    else:
        prev_record: TrackerStats = prev_records[0]
        if prev_record.rating != rating:
            should_save = True
    if should_save:
        stat = TrackerStats(timestamp=timestamp, rating=rating, tier=tier, division=division, icon_url=icon_url)
        await stat.save()


if __name__ == "__main__":

    asyncio.run(get_stats())
