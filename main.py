import json
import time

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from tracker_scraper import get_stats
from model import *
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

origins = ["*"]

current_match: Optional[Match] = Match(match_id='None')

score_queue: List[Dict] = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run_main():
    while True:
        await get_stats()
        await asyncio.sleep(5)


@app.on_event("startup")
async def start_db():
    await init_db()
    asyncio.create_task(run_main())


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.j2",  {"request": request})


@app.post("/bakkes")
async def bakkes(request: Request):
    print(f"Raw data from bakkes {await request.body()}")
    print(f"Got message from bakkes {await request.json()}")
    return {"result": "success"}


@app.post("/rl_event/{event_name}")
async def rl_event(event_name: str, event: Request):
    global current_match
    req_info = await event.json()
    new_event = None
    # # Do this one time.. record a game so I don't have to play over and over again to get all the features
    # post_data = {
    #     "event_name": event_name,
    #     "post_data": req_info
    # }
    # with open("one_match.json", "a") as outfile:
    #     json.dump(post_data, outfile, indent=4)
    #     outfile.write(",\n")
    #
    if event_name == 'rosterChange':
        new_event = EventRosterChange(**req_info)
        if not current_match.is_roster_locked:
            roster = new_event.data.roster
            current_match.players = roster

    elif event_name == 'playerJoined':
        new_event = PlayerJoined(**req_info)
    elif event_name == 'playerLeft':
        new_event = PlayerLeft(**req_info)
    elif event_name == 'score':
        new_event = Score(**req_info)
        current_match.add_player_score(new_event.player)
    elif event_name == 'opposingTeamGoal':
        new_event = OpposingTeamGoal(**req_info)
    elif event_name == 'action_points':
        new_event = ActionPoints(**req_info)
    elif event_name == 'teamGoal':
        new_event = TeamGoal(**req_info)
    elif event_name == 'death':
        new_event = Death(**req_info)
    elif event_name == 'victory':
        new_event = Victory(**req_info)
    elif event_name == 'defeat':
        new_event = Defeat(**req_info)
    elif event_name == 'matchStart':
        new_event = MatchStart(**req_info)
    elif event_name == 'matchEnd':
        new_event = MatchEnd(**req_info)
    elif event_name == 'goal':
        new_event = Goal(**req_info)
    elif event_name == 'gameState':
        new_event = GameState(**req_info)
        current_match.game_state = new_event.data
        print(f"GameState: {new_event.data}")
        if new_event.data == "Active":
            current_match.is_roster_locked = True
    elif event_name == 'pseudo_match_id':
        new_event = PseudoMatchId(**req_info)
        if new_event.data == 'None':
            current_match = Match(match_id=new_event.data)
        else:
            current_match.match_id = new_event.data
    elif event_name == 'arena':
        new_event = Arena(**req_info)
    elif event_name == 'gameMode':
        new_event = GameMode(**req_info)
        current_match.game_mode = new_event.data
    elif event_name == 'matchType':
        new_event = MatchType(**req_info)
    elif event_name == 'gameType':
        new_event = GameType(**req_info)
    elif event_name == 'ranked':
        new_event = Ranked(**req_info)
    elif event_name == 'server_info':
        new_event = ServerInfo(**req_info)
    else:
        print("JHS: Unknown event")
        print(req_info)
        with open("event.json", "a") as outfile:
            json.dump(req_info, outfile, indent=4)
            outfile.write(",\n")
    if new_event:
        await new_event.save()
    return {"result": "success"}


@app.post("/rl_info")
async def rl_info(info: Request):
    req_info = await info.json()
    with open("info.json", "a") as outfile:
        json.dump(req_info, outfile, indent=4)
        outfile.write(",\n")


@app.get("/roster_data")
async def roster_data():
    if current_match and current_match.is_roster_locked:
        return current_match.players
    return None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8822, log_level="debug")
