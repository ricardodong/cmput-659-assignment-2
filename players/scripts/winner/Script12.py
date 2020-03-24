
from players.player import Player
import random
from players.scripts.DSL import DSL

class Script12(Player):

    def __init__(self):
        self._counter_calls = []
        for i in range(1):
            self._counter_calls.append(0)
            
    def get_counter_calls(self):
        return self._counter_calls 

    def get_action(self, state):
        actions = state.available_moves()
        
        for a in actions:
        
            if DSL.hasWonColumn(state) and DSL.isStopAction(a):
                self._counter_calls[0] += 1
                return a
                    
        return actions[0]
                    