from game import Board, Game
from players.scripts.DSL import DSL
from vanilla_uct_player import Vanilla_UCT
import random
from copy import deepcopy
from math import exp


# tree node used for proposal function to sample
class proposal_function_node:
    def __init__(self, dsl, rule, type, parent=None):
        self.dsl = dsl
        self.rulePartial = rule  # raw rule with children not translated
        self.parent = parent     # parent node
        self.children = []       # children nodes
        self.type = type         # rule "B1"'s type is "B", "isStopAction"'s type is B1, the parent can be "B1 and B1"
        self.generatedRule = ''  # real partial rule with children translated

    # re-expand current node, generate all children and also generate the partial rule represent by this node
    # partial rule stored in self.generatedRule
    def expand(self):
        self.children = []
        self.generatedRule = ''
        if self.rulePartial in self.dsl._grammar:
            childRule = random.choice(self.dsl._grammar[self.rulePartial])
            newChild = proposal_function_node(self.dsl, childRule, self.rulePartial, self)
            newChild.expand()
            self.generatedRule = deepcopy(newChild.generatedRule)
            self.children.append(newChild)
        elif len(self.rulePartial.split(' ')) > 1:
            dividedRule = self.rulePartial.split(' ')
            for i in dividedRule:
                if i in self.dsl._grammar:
                    childRule = random.choice(self.dsl._grammar[i])
                    newChild = proposal_function_node(self.dsl, childRule, i, self)
                    newChild.expand()
                    self.generatedRule += newChild.generatedRule
                    self.children.append(newChild)
                else:
                    if i == 'and':
                        self.generatedRule += ' and '
                    else:
                        self.generatedRule += i
        else:
            self.generatedRule = deepcopy(self.rulePartial)

    # generate the rule this node have, based on the current node in the tree
    # the old generated rule is abandoned
    # the generated result is self.generatedRule
    def geneRule(self):
        self.generatedRule = ''
        childIndex = 0
        dividedRule = self.rulePartial.split(' ')
        for i in dividedRule:
            if i in self.dsl._grammar:
                self.children[childIndex].geneRule()
                self.generatedRule += self.children[childIndex].generatedRule
                childIndex += 1
            else:
                if i == 'and':
                    self.generatedRule += ' and '
                else:
                    self.generatedRule += i

    # change the current node to another random one
    def mutate(self):
        self.rulePartial = random.choice(self.dsl._grammar[self.type])
        self.expand()

    # get all tree node under one root (rule), except itself
    def getAllChildNodes(self):

        nodes = []
        for child in self.children:
            nodes.append(child)
            grandChildren = child.getAllChildNodes()
            nodes += grandChildren
        return nodes


def gamePlay(rounds=20):
    first = Vanilla_UCT(1, 100)  # default value
    state_and_action = []

    for _ in range(rounds):
        game = Game(n_players=2, dice_number=4, dice_value=3, column_range=[2, 6],
                    offset=2, initial_height=1)

        is_over = False

        number_of_moves = 0
        current_player = game.player_turn
        while not is_over:
            moves = game.available_moves()
            if game.is_player_busted(moves):
                if current_player == 1:
                    current_player = 2
                else:
                    current_player = 1
                continue
            else:
                if game.player_turn == 1:
                    chosen_play = first.get_action(game)
                else:
                    chosen_play = first.get_action(game)

                state_and_action.append([game.clone(), chosen_play])

                if chosen_play == 'n':
                    if current_player == 1:
                        current_player = 2
                    else:
                        current_player = 1
                game.play(chosen_play)
                number_of_moves += 1

            who_won, is_over = game.is_finished()

            if number_of_moves >= 200:
                is_over = True
                print('No Winner!')

    return state_and_action


# remove the training data satisfied by the previous best rule
def remove_training_data(data, rule):
    newData = deepcopy(data)
    for state_and_action in newData:
        state = state_and_action[0]
        chosen_action = state_and_action[1]
        used = False
        error = 0
        for a in state.available_moves():
            if eval(rule):
                used = True
                if a != chosen_action:
                    error += 1
                break
        if not used and state.available_moves()[0] != chosen_action:
            error += 1
        if error == 0:
            newData.remove(state_and_action)
    return newData


def train_rule(trainingData):
    # init parameters
    newDsl = DSL()
    sampleNumber = 1000
    sampledRule = []

    prevRule = proposal_function_node(newDsl, 'B', 'S')
    prevRule.expand()
    prevScore = 0

    # sample "sampleNumber" times, create less samples than this number
    for i in range(sampleNumber):
        # generate a new sample
        # newRule.generatedRule is the newly sampled rule
        newRule = deepcopy(prevRule)
        error = 0
        allNodes = []
        allNodes += newRule.getAllChildNodes()
        mutateNode = random.choice(allNodes)
        mutateNode.mutate()
        newRule.geneRule()

        # evaluate possible new sample
        never_used = True
        for state_and_action in trainingData:
            state = state_and_action[0]
            chosen_action = state_and_action[1]
            used = False
            for a in state.available_moves():
                if eval(newRule.generatedRule):
                    used = True
                    never_used = False
                    if a != chosen_action:
                        error += 1
                    break
            if not used and state.available_moves()[0] != chosen_action:
                error += 1

        # decide sample or not
        if never_used:
            continue
        score = exp(-0.5 * error)
        if prevScore > 0 and score / prevScore < 1:
            ran_num = random.uniform(0.0, 1.0)
            if ran_num < score / prevScore:
                sampledRule.append((newRule, error))
                prevRule = deepcopy(newRule)
                prevScore = score
        else:
            sampledRule.append((newRule, error))
            prevRule = deepcopy(newRule)
            prevScore = score

    # best sampled rule is the rule with least errors
    bestRule = min(sampledRule, key=lambda x: x[1])
    return bestRule[0].generatedRule



trainingData = gamePlay(20)
print("finish training")
for i in range(5):
    rule = train_rule(trainingData)
    print('r' + str(i) + ': ' + rule)
    trainingData = remove_training_data(trainingData, rule)



