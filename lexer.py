from enum import Enum
from typing import List

import re
num_pattern = re.compile("([0-9]+(\\.[0-9]+)?)")
comment_pattern = re.compile("//.*")

class TokenType(Enum):
    # Keywords
    CTMC = "ctmc"
    DTMC = "dtmc"
    ENDMODULE = "endmodule"
    MDP  = "mdp"
    MODULE = "module"

    # Symbols
    COLON = ":"

    # Other tokens
    NUM = "num"
    OTHER = "other"

class Token:
    tokentype: TokenType
    value: str
    
    def __init__(self, value):
        self.value = value
        match value:
            case "ctmc":
                self.tokentype = TokenType.CTMC
            case "dtmc":
                self.tokentype = TokenType.DTMC
            case "endmodule":
                self.tokentype = TokenType.ENDMODULE
            case "mdp":
                self.tokentype = TokenType.MDP
            case "module":
                self.tokentype = TokenType.MODULE
            case ":":
                self.tokentype = TokenType.COLON
            case _:
                if num_pattern.match(value):
                    self.tokentype = TokenType.NUM
                else:
                    self.tokentype = TokenType.OTHER
    def __repr__(self):
        return f"[{self.tokentype}: {self.value}]"

def lex(file: str) -> List[List[Token]]:
    lines = []
    for line in file.split("\n"):
        lines.append(line)
    tokenlines = []
    for line in lines:
        tokenline = []
        for strtok in line.split():
            # Ignore everything after single line comments
            if (comment_pattern.match(strtok)):
                break
            tokenline.append(Token(strtok))
        if len(tokenline) > 0:
            tokenlines.append(tokenline)
    return tokenlines
