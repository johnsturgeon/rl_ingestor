import asyncio
import os
from typing import List, Optional, Union, Dict

from beanie import Document, UnionDoc, init_beanie
from pydantic import BaseModel, validator
import motor.motor_asyncio


async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv('MONGO_URI')
    )
    document_models = [
        ActionPoints,
        Arena,
        Death,
        Defeat,
        Event,
        EventRosterChange,
        GameState,
        GameMode,
        GameType,
        Goal,
        MatchEnd,
        MatchStart,
        MatchType,
        OpposingTeamGoal,
        PlayerJoined,
        PlayerLeft,
        PseudoMatchId,
        Ranked,
        Score,
        ServerInfo,
        SimplePlayerEvent,
        TeamGoal,
        Victory
    ]
    await init_beanie(database=client.rocket_league, document_models=document_models)


class Event(UnionDoc):

    class Settings:
        name = "events"

    @staticmethod
    async def get_latest_match_id():
        latest_events = await Event.all(limit=1, sort="-timestamp").to_list()
        if latest_events:
            latest_event = latest_events[0]
            return latest_event.match_id
        return None


class BaseEventData(BaseModel):
    name: str
    timestamp: int
    match_id: str

    class Settings:
        union_doc = Event


class Player(BaseModel):
    steam_id: int
    score: int
    goals: int
    name: str
    state: int
    team_score: int
    team: int
    local: int
    index: int


class WinLossData(BaseModel):
    team_score: int


class Roster(BaseModel):
    roster: List[Player]


class EventRosterChange(Document, BaseEventData):
    data: Roster

    class Settings:
        union_doc = Event

    @staticmethod
    async def get_latest_roster_change(match_id: str):
        roster_changes = await EventRosterChange.find(
            EventRosterChange.match_id == match_id
        ).sort("-timestamp").limit(1).to_list()
        if not roster_changes:
            return None
        return roster_changes[0]


class SimpleEvent(Document, BaseEventData):
    data: str | None = ...

    @validator('data')
    def empty_str_to_none(cls, v):
        if v is None:
            return 'None'
        return v


class SimplePlayerEvent(Document, BaseEventData):
    data: Player

    @property
    def player(self):
        return self.data


class PlayerJoined(SimplePlayerEvent):
    pass


class PlayerLeft(SimplePlayerEvent):
    pass


class Score(SimplePlayerEvent):
    pass


class OpposingTeamGoal(SimplePlayerEvent):
    pass


class TeamGoal(SimplePlayerEvent):
    pass


class ActionPoints(SimpleEvent):
    pass


class GameState(SimpleEvent):
    pass


class Arena(SimpleEvent):
    pass


class Ranked(SimpleEvent):
    pass


class GameMode(SimpleEvent):
    pass


class GameType(SimpleEvent):
    pass


class MatchType(SimpleEvent):
    pass


class PseudoMatchId(SimpleEvent):
    pass


class Death(SimpleEvent):
    pass


class Goal(SimplePlayerEvent):
    pass


class MatchEnd(SimpleEvent):
    pass


class ServerInfo(SimpleEvent):
    pass


class MatchStart(SimpleEvent):
    pass


class Victory(Document, BaseEventData):
    data: WinLossData


class Defeat(Document, BaseEventData):
    data: WinLossData


class TrackerDailyMMR(Document):
    rating: int
    tier: str
    division: str
    tierId: int
    divisionId: int
    collectDate: str

    class Settings:
        name = "tracker_daily_mmr"


class TrackerStats(Document):
    timestamp: int
    rating: int
    tier: str
    division: str
    icon_url: str

    class Settings:
        name = "tracker_stats"


class Match(BaseModel):
    match_id: str
    game_mode: Optional[str]
    game_state: Optional[str]
    is_roster_locked: Optional[bool] = False
    roster_sent: Optional[bool] = False
    players: Optional[List[Player]]
    action_points: Optional[List[ActionPoints]]

    def add_player_score(self, player: Player):
        new_roster = []
        for current_player in self.players:
            if player.name == current_player.name:
                new_roster.append(player)
            else:
                new_roster.append(current_player)
        self.players = new_roster

