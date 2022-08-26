class NoSQL(Exception):
    
    def __init__(self):
        self.message = "No sql statemtnt is provided. Please refer to README.md for more information."
   
    def __str__(self):
        return(repr(self.message))

class NoTimestreamDimension(Exception):
    
    def __init__(self):
        self.message = "No dimesnsion is provided. Each record contains an array of dimensions (minimum 1).Please refer to README.md for more information."
   
    def __str__(self):
        return(repr(self.message))        

class WrongLengthForInput(Exception):
    
    def __init__(self, message):
        self.message = message
   
    def __str__(self):
        return(repr(self.message))  

class WrongFormattedInput(Exception):
    
    def __init__(self, message):
        self.message = message
   
    def __str__(self):
        return(repr(self.message))                                          