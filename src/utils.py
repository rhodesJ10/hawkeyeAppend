import json
import os
import time


DATA_PATH = 'C:/Users/James Rhodes Gym 1/Documents/EPL Second Spectrum/Season 22-23/UCL/Hawkeye/Milan-Salzburg/centroids/'
OUTPUT_PATH = 'C:/Users/James Rhodes Gym 1/Anaconda3/hawkeyeFiles2/output/Milan_output.jsonl'

class KEYS:
    DETAILS = "details"
    PLAYERS = "players"
    TEAMID = "teamId"
    JERSEY_NUM = "jerseyNumber"
    PLAYER_ID = "heId"

    SAMPLES = "samples"
    CENTROID = "centroid"
    PEOPLE = "people"
    PERSON_ID = "personId"
    ROLE = "role"
    NAME = "name"
    ROLES = ["Outfielder", "Goalkeeper"]

    TEAMS = "teams"
    ID = "id"
    UEFAID = "uefaId"

    SEQUENCES = "sequences"
    SEGMENT = "segment"
    MATCH_MIN = "match-minute"
    STOPPAGE = "stoppage-minute"

    #TEAMS
    HOME = "home"
    AWAY = "away"

    ### CENTROIDS KEYS
    SPEED = "speed"
    SPEED_UNIT = "mps" #change to "mph" to use miles per hour

    POSITION = "pos"

    TIME = "time"
    #########################################################
    ### OUTPUT KEYS
    OUTPUT_PERIOD = "period"
    OUTPUT_FRAME_IDX = "frameIdx"
    OUTPUT_GAME_CLOCK = "gameClock"
    OUTPUT_WALL_CLOCK = "wallClock"
    OUTPUT_HOME_PLAYERS = "homePlayers"
    OUTPUT_AWAY_PLAYERS = "awayPlayers"
    OUTPUT_PLAYER_ID = "playerId"
    OUTPUT_NUMBER = "number"
    OUTPUT_COORDINATES = "xyz"
    OUTPUT_SPEED = "speed"
    OUTPUT_OPTA_ID = "optaId"
    OUTPUT_BALL = "ball"
    OUTPUT_LIVE = "live"
    OUTPUT_LAST_TOUCH = "lastTouch"

def startTimer(msg):
    print(msg)
    return time.perf_counter()
def endTimer(msg, start):
    finish = time.perf_counter()
    print(msg+" {:6f}s\n".format(finish-start))


def loadJson(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data


def readDocuments():
    start = startTimer("Reading documents...")

    data = []
    for f in os.listdir(DATA_PATH):
        print(f"Loading: {f}")
        data.append(loadJson(f"{DATA_PATH}{f}"))
    
    endTimer("Documents loaded in", start)
    
    return data


#Creates a line for the final JSONL    
def createJSONLine(period, frameIdx, gameClock, periodClock, homePlayers, awayPlayers):
    line = "{"
    line += f'"{KEYS.OUTPUT_PERIOD}": {period}, '
    line += f'"{KEYS.OUTPUT_FRAME_IDX}": {frameIdx}, '
    line += f'"{KEYS.OUTPUT_GAME_CLOCK}": {periodClock}, '
    line += f'"{KEYS.OUTPUT_WALL_CLOCK}": 9999999999999, '
    line += f'"{KEYS.OUTPUT_HOME_PLAYERS}": [{playersSamples(homePlayers, period, gameClock)}], '
    line += f'"{KEYS.OUTPUT_AWAY_PLAYERS}": [{playersSamples(awayPlayers, period, gameClock)}], '
    line += f'"{KEYS.OUTPUT_BALL}": {{"{KEYS.OUTPUT_COORDINATES}": [0,0,0], "{KEYS.OUTPUT_SPEED}": 0}}, '
    line += f'"{KEYS.OUTPUT_LIVE}": true, '
    line += f'"{KEYS.OUTPUT_LAST_TOUCH}": "{KEYS.HOME}"'
    line += "}"
    return line

def playerSampleToString(sample, player):
    line = "{"
    line += f'"{KEYS.OUTPUT_PLAYER_ID}": "{player.playerId}", '
    line += f'"{KEYS.OUTPUT_NUMBER}": "{player.number}", '
    line += f'"{KEYS.OUTPUT_COORDINATES}": [{round(sample[KEYS.POSITION][0], 2)}, {round(sample[KEYS.POSITION][1], 2)}, 0.0], '
    line += f'"{KEYS.OUTPUT_SPEED}": {round(sample[KEYS.SPEED], 2)}, '
    line += f'"{KEYS.OUTPUT_OPTA_ID}": "{player.optaId}"'

    line += "}"
    return line

def playersSamples(samples, period, frameIdx):
    elements = []
    for player in samples:
        sample = player.getSample(period, frameIdx)
        if sample is None:
            continue
        elements.append(playerSampleToString(sample, player))
    
    line = ", ".join(elements)
    return line


def exportDataToJson(data):
    fileData = "\n".join(data)
    with open(OUTPUT_PATH, "w") as f:
        f.write(fileData)
