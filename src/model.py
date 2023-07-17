from copy import copy, deepcopy
from math import ceil, floor
from utils import KEYS, startTimer, endTimer, createJSONLine, exportDataToJson

TIME_FRAME = 0.04

################################
######### PLAYER CLASS #########
################################

class Player:    
    def __init__(self, playerId, number, optaId):
        self.playerId = playerId
        self.number = number
        self.optaId = optaId
        #To be indexed with time
        self.samples = {
            1: {},
            2: {}
        }

    #Add a sample to the player data.
    #This compute the mean of two samples to create a TIME_FRAME long constant sampling.
    def addSample(self, centroid, period, minute):
        #Raw time
        time = (minute-1)*60 + centroid[KEYS.TIME] 
        #Time frames indexes
        lowTimeIdx = round(floor(time/TIME_FRAME)*TIME_FRAME, 2)
        upTimeIdx = round(ceil(time/TIME_FRAME)*TIME_FRAME, 2)
        
        #Raw sample
        sample = {
            KEYS.TIME: time,
            KEYS.SPEED: centroid[KEYS.SPEED][KEYS.SPEED_UNIT],
            KEYS.POSITION: [centroid[KEYS.POSITION][0], centroid[KEYS.POSITION][1], 0]
        }
        
        if time == lowTimeIdx:
            self.samples[period][lowTimeIdx] = deepcopy(sample)
        elif time == upTimeIdx:
            self.samples[period][upTimeIdx] = deepcopy(sample)

        lowerSample = self.samples[period][lowTimeIdx] if lowTimeIdx in self.samples[period].keys() else None
        if lowerSample is None:
            self.samples[period][lowTimeIdx] = deepcopy(sample)
            if minute == 1:
                self.samples[period][lowTimeIdx][KEYS.TIME] = lowTimeIdx
        elif lowTimeIdx != lowerSample[KEYS.TIME]:
            #Linear mean between the sample with time highest lower and lowest higher nearest to the framed time
            meanSample = {
                KEYS.TIME: lowTimeIdx,
                KEYS.SPEED: self.getLinearMean(lowTimeIdx, lowerSample[KEYS.TIME], sample[KEYS.TIME], lowerSample[KEYS.SPEED], sample[KEYS.SPEED]),
                KEYS.POSITION: [self.getLinearMean(lowTimeIdx, lowerSample[KEYS.TIME], sample[KEYS.TIME], lowerSample[KEYS.POSITION][0], sample[KEYS.POSITION][0]), self.getLinearMean(lowTimeIdx, lowerSample[KEYS.TIME], sample[KEYS.TIME], lowerSample[KEYS.POSITION][1], sample[KEYS.POSITION][1]), 0]
            }
            self.samples[period][lowTimeIdx] = meanSample
        
        if upTimeIdx in self.samples[period].keys():
            upperSample = self.samples[period][upTimeIdx]
            #Go on untill finds 
            if sample[KEYS.TIME] > upperSample[KEYS.TIME]:
                #This case means that you can use data sampled closer to the time frame that you have to mean.
                #You can discard previous sample data
                self.samples[period][upTimeIdx] = deepcopy(sample)
            #Allow adding samples not in order of minutes
            elif upperSample[KEYS.TIME] > upTimeIdx:
                #This is verified only when an ordered sample set (minute sample set) meets a higher minute sample set that has been already analyzed
                meanSample = {
                    KEYS.TIME: upTimeIdx,
                    KEYS.SPEED: self.getLinearMean(upTimeIdx, sample[KEYS.TIME], upperSample[KEYS.TIME], sample[KEYS.SPEED], upperSample[KEYS.SPEED]),
                    KEYS.POSITION: [self.getLinearMean(upTimeIdx, sample[KEYS.TIME], upperSample[KEYS.TIME], sample[KEYS.POSITION][0], upperSample[KEYS.POSITION][0]), self.getLinearMean(upTimeIdx, sample[KEYS.TIME], upperSample[KEYS.TIME], sample[KEYS.POSITION][1], upperSample[KEYS.POSITION][1]), 0]
                }
                self.samples[period][upTimeIdx] = meanSample
        else:
            self.samples[period][upTimeIdx] = deepcopy(sample)
        
        return upTimeIdx
    
    def getSamples(self):
        if len(self.samples[1].keys()) == 0 and len(self.samples[2].keys()) == 0:
            return None
        else:
            return self.samples
        
    def getSample(self, period, timeStamp):
        if period in self.samples.keys() and timeStamp in self.samples[period].keys():
            return self.samples[period][timeStamp]
        else:
            return None

    def getLinearMean(self, time, t1, t2, s1, s2):
        mean = (time - t1) / (t2 - t1) * (s2 - s1) + s1
        return mean
    


################################
########## GAME CLASS ##########
################################

class Game:
    def __init__(self):
        # period, frameIdx, gameClock, wallClock to be calculated
        self.homeUefaId = ""
        self.awayUefaId = ""
        # Lists of Player objects
        self.players = {
            KEYS.HOME: {},
            KEYS.AWAY: {}
        }

        #Indexed with time
        #Values: true and false !! notice not True and False
        self.live = {
            1: {},
            2: {}
        }
        #Indexed with time
        #Values: home and away
        self.lastTouches = {
            1: {},
            2: {}
        }

        self.maxTime = {
            1: 0,
            2: 0
        }
    
    def getPlayer(self, uefaId):
        return self.players[KEYS.HOME][uefaId] if uefaId in self.players[KEYS.HOME] else self.players[KEYS.AWAY][uefaId]

    def setPlayers(self, players):
        for player in players:
            teamUefaId = player[KEYS.TEAMID][KEYS.UEFAID]
            playerUefaId = player[KEYS.ID][KEYS.UEFAID]

            team = KEYS.HOME if teamUefaId == self.homeUefaId else KEYS.AWAY
            if playerUefaId not in self.players[team].keys():
                self.players[team][playerUefaId] = Player(player[KEYS.ID][KEYS.PLAYER_ID], player[KEYS.JERSEY_NUM], playerUefaId)

    def addLiveStatus(self, status, time, period):
        pass

    def addLastTouch(self, teamLastTouch, time, period):
        pass

    def setTeams(self, data):
        self.homeUefaId = data[0][KEYS.ID][KEYS.UEFAID]
        self.awayUefaId = data[1][KEYS.ID][KEYS.UEFAID]
    
    def isPlayer(self, sample):
        return True if sample[KEYS.ROLE][KEYS.NAME] in KEYS.ROLES else  False

    def deleteEmptyPlayers(self):
        toBeDelated = []
        for team in [KEYS.HOME, KEYS.AWAY]:
            for player in self.players[team].keys():
                if self.players[team][player].getSamples() is None:
                    toBeDelated.append([team, player])
        for team, player in toBeDelated:
            del self.players[team][player]

    # Load raw data into Game and Players objects
    def transformData(self, data):
        start = startTimer("Transforming data...")
        
        self.setTeams(data[0][KEYS.DETAILS][KEYS.TEAMS])
        self.setPlayers(data[0][KEYS.DETAILS][KEYS.PLAYERS])

        for minute in data:
            period = minute[KEYS.SEQUENCES][KEYS.SEGMENT]
            matchMinute = minute[KEYS.SEQUENCES][KEYS.MATCH_MIN]
            if KEYS.STOPPAGE in minute[KEYS.SEQUENCES].keys():
                matchMinute += minute[KEYS.SEQUENCES][KEYS.STOPPAGE]

            for sample in minute[KEYS.SAMPLES][KEYS.PEOPLE]:
                if self.isPlayer(sample):
                    player = self.getPlayer(sample[KEYS.PERSON_ID][KEYS.UEFAID])
                    time = player.addSample(sample[KEYS.CENTROID][0], period, matchMinute)
                    
                    #Set max time
                    if time > self.maxTime[period]:
                        self.maxTime[period] = time
                

        self.deleteEmptyPlayers()
        endTimer("Data transformed in ", start)


    def createJson(self):
        start = startTimer("Creating JSONL...")
        print(self.maxTime[1])
        print(self.maxTime[2])

        jsonLines = []
        gameClock = 0
        index = 0
        for period in self.maxTime.keys():
            periodClock = 0
            while gameClock <= self.maxTime[period]:
                homePlayers = []
                awayPlayers = []
                for team in [KEYS.HOME, KEYS.AWAY]:
                    for player in self.players[team].values():
                        playerSample = player.getSample(period, gameClock)
                        if playerSample != None:
                            if team == KEYS.HOME:
                                homePlayers.append(player)
                            else:
                                awayPlayers.append(player)
                jsonLines.append(createJSONLine(period, index, gameClock, periodClock, homePlayers, awayPlayers))

                gameClock += TIME_FRAME
                gameClock = round(gameClock, 2)
                index += 1
                periodClock += TIME_FRAME
                periodClock = round(periodClock, 2)
        
        exportDataToJson(jsonLines)
        endTimer("JSONL created in ", start)

