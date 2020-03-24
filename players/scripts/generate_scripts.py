from players.scripts.Script import Script
from players.scripts.DSL import DSL
from game import Board, Game

import importlib
import os
from copy import deepcopy
from random import choice, uniform


def ESZ():
    # parameters
    populationSize = 30
    numOfGene = 30
    numOfTour = 5
    numOfElite = 10
    numOfRounds = 10
    mutateRate = 0.5

    # init population
    dslExample = DSL()
    scripts = dslExample.generateRandomScript(populationSize)
    for i in scripts:
        i.saveFile('')
    scriptIdCounter = populationSize  # show the id of the next script
    numOfWinRule = []

    # evaluate
    for _ in range(numOfGene):
        numOfWinRule.append(count_winning_rule(scripts))
        print(count_winning_rule(scripts))
        Evaluate(scripts, numOfRounds)  # change the fitness numbers of scripts
        # get elites
        nextGene = elite(scripts, numOfElite)
        # clear fitness and call count
        for i in scripts:
            i.clearAttributes()
        while len(nextGene) < len(scripts):
            p1, p2 = tournament(scripts, numOfTour, numOfRounds)
            c = crossoverBackup(p1, p2, scriptIdCounter)
            while len(c.getRules()) == 0:
                c = crossoverBackup(p1, p2, scriptIdCounter)
            mutate(c, mutateRate, dslExample)
            c.saveFile('')
            scriptIdCounter += 1
            nextGene.append(c)
        scripts = deepcopy(nextGene)

    # keep the best scripts
    Evaluate(scripts, numOfRounds)
    sortedScripts = sorted(scripts, key= lambda x:x.getFitness(), reverse=True)
    winnerPath = 'winner/'
    if not os.path.exists(os.path.split(winnerPath)[0]):
        os.makedirs(os.path.split(winnerPath)[0])
    sortedScripts[0].saveFile(winnerPath)

    for i in range(numOfGene):
        print("# of scripts containing winning rule in generation " + str(i) + ": ", str(numOfWinRule[i]))


def count_winning_rule(scripts):
    count = 0
    for i in scripts:
        rules = i.getRules()
        for j in rules:
            if "DSL.hasWonColumn(state) and DSL.isStopAction(a)" in j[0] or \
                    "DSL.isStopAction(a) and DSL.hasWonColumn(state)" in j[0]:
                count += 1
            # if "DSL.actionWinsColumn(state,a)" in j[0]:
            #     count += 1
    return count


def Evaluate(population, numberOfRounds):
    # population are scripts
    for script in population:
        filename = 'Script' + str(script.getId())
        module = importlib.import_module('players.scripts.' + filename)
        class_ = getattr(module, filename)
        current_script = class_()
        for otherScript in population:
            if script.getId() == otherScript.getId():
                continue
            filename2 = 'Script' + str(otherScript.getId())
            module = importlib.import_module('players.scripts.' + filename2)
            class_ = getattr(module, filename2)
            other_script = class_()
            script.addFitness(gamePlay(current_script, other_script, numberOfRounds)[0])
            script.addFitness(gamePlay(other_script, current_script, numberOfRounds)[1])
        scriptCounterCalls = deepcopy(current_script.get_counter_calls())
        script.remove_unused_rules(scriptCounterCalls)
    return


def gamePlay(player1, player2, rounds=20):
    # evaluation start
    victories_1 = 0
    victories_2 = 0
    for _ in range(rounds):
        game = Game(n_players=2, dice_number=4, dice_value=3, column_range=[2, 6],
                    offset=2, initial_height=1)

        is_over = False
        who_won = None

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
                    chosen_play = player1.get_action(game)
                else:
                    chosen_play = player2.get_action(game)
                if chosen_play == 'n':
                    if current_player == 1:
                        current_player = 2
                    else:
                        current_player = 1
                # print('Chose: ', chosen_play)
                # game.print_board()
                game.play(chosen_play)
                # game.print_board()
                number_of_moves += 1

                # print()
            who_won, is_over = game.is_finished()

            if number_of_moves >= 200:
                is_over = True
                who_won = -1
                # print('No Winner!')

        if who_won == 1:
            victories_1 += 1
        if who_won == 2:
            victories_2 += 1
    # print(victories_current, victories_other)
    # print('Player ', str(script.getId()), ': ', victories_current / (victories_current + victories_other))
    # print('Player ', str(otherScript.getId()), ': ', victories_other / (victories_current + victories_other))
    return victories_1, victories_2


def elite(scripts, numOfElite):
    sortedScripts = sorted(scripts, key= lambda x:x.getFitness(), reverse=True)
    elites = []
    for i in range(numOfElite):
        if sortedScripts[i].getFitness() > 0:
            elites.append(sortedScripts[i])
        else:
            elites.append(sortedScripts[0])
    return elites


def tournament(scripts, numOfTour, numOfRounds):
    attender = []
    for _ in range(numOfTour):
        newAttender = choice(scripts)
        while newAttender in attender:
            newAttender = choice(scripts)
        attender.append(newAttender)

    Evaluate(attender, numOfRounds)
    sortedAttender = sorted(attender, key= lambda x:x.getFitness(), reverse=True)
    for i in attender:
        i.clearAttributes()
    return sortedAttender[0], sortedAttender[1]
    # best 2 players


def crossover(p1, p2, scriptIdCounter):
    childRules = []
    # child rules are combined from parents because parents rules work good
    # we do not want to create new rules in crossover because

    p1RuleLen = len(p1.getRules())
    p2RuleLen = len(p2.getRules())
    splitPoint = int(min(p1RuleLen, p2RuleLen)/2)
    if splitPoint == 0:
        if p1RuleLen == 1 and p2RuleLen == 1:
            childRules.append(p1.getRules()[0])
            childRules.append(p2.getRules()[0])
        elif p1RuleLen == 1 and p2RuleLen > 1:
            childRules.append(p1.getRules()[0])
            for i in range(1, p2RuleLen):
                childRules.append(p2.getRules()[i])
        elif p1RuleLen > 1 and p2RuleLen == 1:
            for i in range(p1RuleLen-1):
                childRules.append(p1.getRules()[i])
            childRules.append(p2.getRules()[0])
        else:
            print("crossover split error")
    else:
        for i in range(splitPoint):
            childRules.append(p1.getRules()[i])
        for i in range(splitPoint, p2RuleLen):
            childRules.append(p2.getRules()[i])

    child = Script(childRules, scriptIdCounter)
    return child


def crossoverBackup(p1, p2, scriptIdCounter):
    childRules = p1.generateSplit()[0] + p2.generateSplit()[1]
    child = Script(childRules, scriptIdCounter)
    return child


def mutate(child, mutateRate, dsl):
    child.mutate(mutateRate, dsl)


ESZ()
