import time

class weather_station:
    windGust1minSpeed:float
    windGust1minDirection:float
    windDataSpeed = []
    windDataDirection = []
    windGust = []
    gustDataCounter:int
    windDataCounter:int

    # report this information
    windSpeed:float
    windDirection:float
    wind2MinAverageMPH:float
    wind2MinAverageDirection:float
    wind10MinGustMPH:float
    wind10MinGustDirection:float

    def __init__(self):
        print("starting weather station")
        self.windGust1minSpeed = 0.0
        self.gustDataCounter = 60
        self.windDataCounter = 120
        self.windGust1minDirection = 0.0
        self.windGust1minSpeed = 0.0
        self.wind2MinAverageMPH = 0.0
        self.wind2MinAverageDirection = 0.0
        self.wind10MinGustDirection = 0.0
        self.wind10MinGustMPH = 0.0
        self.windSpeed = 0.0
        self.windDirection = 0.0

    # run every 1 minute assumes it is called every second
    def _doGusts(self, speed: float, direction:float):
        self.gustDataCounter -= 1
        if speed > self.windGust1minSpeed:
            self.windGust1minSpeed = speed
            self.windGust1minDirection = direction

        if self.gustDataCounter == 0:
            self.gustDataCounter = 60
            # update the 10 minute wind gust statistics every minute
            gdata = (self.windGust1minSpeed, self.windGust1minDirection)
            self.windGust.append( gdata )
            self.windGust1minSpeed = 0
            while len(self.windGust) > 10: # ensure we only have 10 minutes of data
                self.windGust.pop(0)
            gust = (0.0,0.0)
            for g in self.windGust:
                if g[0] > gust[0]:
                    gust = g
            self.wind10MinGustMPH = gust[0]
            self.wind10MinGustDirection = gust[1]

    def addWind(self, speed: float , direction:float):
        self.windDataCounter -= 1
        self.windSpeed = speed
        self.windDirection = direction
        self.windDataSpeed.append( speed )
        self.windDataDirection.append( direction )

        self._doGusts(speed,direction)

        if self.windDataCounter == 0:
            self.windDataCounter = 120
            # time to compute wind statistics (every 2 minutes)
            self._calcWeather()
            self.windDataDirection.clear()
            self.windDataSpeed.clear()

    def _addDirection(self, direction1:float, direction2:float )->float:
        delta = direction1 - direction2
        if delta < -180.0:
            return delta + 360
        elif delta > 180.0:
            return delta - 360
        else:
            return delta

    def _calcWeather(self):
        speedAverage = 0
        for w in self.windDataSpeed:
            speedAverage += w
        self.wind2MinAverageMPH = speedAverage / len(self.windDataSpeed)
        
        sum = self.windDataDirection[0]
        D = self.windDataDirection[0]
        for d in self.windDataDirection[1:]:
            D += self._addDirection(d, D)
            sum += D
        self.wind2MinAverageDirection = sum / len(self.windDataDirection)



