from players.player import Player
from players.scripts.DSL import DSL
import random
from copy import deepcopy

class PlayerTest(Player):

    def get_action(self, state):
        actions = state.available_moves()

        if DSL.isYNAction(actions):
            if DSL.hasAvailableNeuralMarker(state):
                return 'y'
            if DSL.hasWonColumn(state):
                return 'n'
            if DSL.continueBecausehighProbNotBust(state):
                return 'y'
            return random.choice(actions)
        else:
            if DSL.hasAvailableNeuralMarker(state):
                actions = deepcopy(DSL.actionsUseLessMarker(state, actions))

            for a in actions:
                if DSL.isDoubles(a):
                    return a

            for a in actions:
                if DSL.actionWinsColumn(state, a):
                    return a

            # should be later than detect the already progressed one (use of neutral marker)
            # newActions = []
            # if DSL.hasAvailableNeuralMarker(state):
            #     for a in actions:
            #         if DSL.actionEasyToPrograss(state, a):
            #             newActions.append(a)
            # if newActions:
            #     actions = deepcopy(newActions)

            return random.choice(actions)