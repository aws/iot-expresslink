import re
from common.customExceptions import *

def checkInputLength(self, min_length, max_length, input, resource_name):
        if len(input) < min_length or len(input) > max_length:
            raise WrongLengthForInput(f"Invalid input length for {resource_name}'s name. Check the README.md file for more details.")

def checkInputPattern(self, pattern, input, resource_name):
        if not re.match(pattern, input):
            raise WrongFormattedInput(f"Invalid input pattern for {resource_name}'s name. Check the README.md file for more details.")  