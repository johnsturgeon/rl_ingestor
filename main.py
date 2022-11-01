import json
import uvicorn
from beanie import init_beanie
from beanie.odm.queries.find import FindOne
from fastapi import FastAPI
from starlette.responses import StreamingResponse

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


@app.on_event("startup")
async def start_db():
    await init_db()


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.j2",  {"request": request})


@app.post("/rl_event/{event_name}")
async def rl_event(event_name: str, event: Request):
    global current_match
    req_info = await event.json()
    new_event = None
    if event_name == 'rosterChange':
        new_event = EventRosterChange(**req_info)
        roster = new_event.data.roster
        current_match.players = roster
    elif event_name == 'playerJoined':
        new_event = PlayerJoined(**req_info)
    elif event_name == 'playerLeft':
        new_event = PlayerLeft(**req_info)
    elif event_name == 'score':
        new_event = Score(**req_info)
        current_match.add_player_score(new_event.data, timestamp=new_event.timestamp)
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
        if new_event.data == "Active":
            if len(current_match.roster) >= 4:
                current_match.is_roster_locked = True
            else:
                print(f"Active match without full roster!")
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


@app.get("/match_data")
async def match_data():
    if current_match:
        return current_match
    else:
        print("No match yet")
        return {
            "players": [{
                "name": "GDH",
                "score": 111,
                "goals": 111,
                "team_score": 2
            }]
        }


@app.get("/roster_data")
async def roster_data():
    response = StreamingResponse(get_roster(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


async def get_roster() -> Dict:
    while True:
        if current_match:
            if current_match.is_roster_locked and not current_match.roster_sent:
                current_match.roster_sent = True
                print(f"Sending Roster!: {current_match.roster}")
                json_data = json.dumps(current_match.roster)
                print(f"sending ROSTER DATA: {json_data}")
                yield f"data:{json_data}\n\n"
        await asyncio.sleep(1)


@app.get("/score_data")
async def score_data():
    response = StreamingResponse(score_dequeue(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


async def score_dequeue() -> Dict:
    while True:
        if current_match:
            if current_match.player_scores:
                print(f"All Scores: {current_match.player_scores}")
                score = current_match.player_scores.pop(0)
                json_data = json.dumps(score)
                print(f"sending JSON DATA: {json_data}")
                yield f"data:{json_data}\n\n"
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8822, log_level="debug")
