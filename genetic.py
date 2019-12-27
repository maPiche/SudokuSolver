# coding=utf-8

## See http://norvig.com/sudoku.html


## Samuel Ducharme   | 20070143
## Marc-Andre Piche  | 783722

## ALGORITHME GENETIQUE

#IDÉE :
#semblable au beam search, mais en utilisant les concepts d'algorithmes genetique pour les sélections d'états successeurs


# Fonction de Norvig
def cross(A, B):
    """Cross product of elements in A and elements in B."""
    return [a + b for a in A for b in B]

## Variables globales
digits   = '123456789'
rows     = 'ABCDEFGHI'
cols     = digits
squares  = cross(rows, cols)
unitlist = ([cross(rows, c) for c in cols] +
            [cross(r, cols) for r in rows] +
            [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')])
units = dict((s, [u for u in unitlist if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s], [])) - {s})
             for s in squares)

##Rajouté par nous
bigSquares = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
solutionCounter = 0
POP = 200 # Taille de la population
MUTATION_CHANCE = 30 #30%
f = open('genetic.txt', 'a')  # fichier log de la performance
f.write("\n \n#Sudoku : " + "Échec/Succès -" + " Nombre d'étapes - " + " Nombre d'échanges - " + " Meilleur solution - \n")

################ Unit Tests ################

# Fonction de Norvig
def test():
    """A set of tests that must pass."""
    assert len(squares) == 81
    assert len(unitlist) == 27
    assert all(len(units[s]) == 3 for s in squares)
    assert all(len(peers[s]) == 20 for s in squares)
    assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                           ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                           ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]
    assert peers['C2'] == {'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'A1', 'A3', 'B1', 'B3'}
    print 'All tests pass.'


################ Parse a Grid ################

# cette fonction est pratiquement la fonction parse_values du code de Norvig, mais au lieu de retourner
# une grille remplie de possibilitée lorsque c'est une grille valide, elle return True
def est_valide(gridValues):
    values = dict((s, digits) for s in squares)
    for s, d in gridValues.items():
        if d in digits and not assign(values, s, d):
            return False  ## (Fail if we can't assign d to square s.)
    return True


# Fonction de Norvig
def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))



# But : prendre une grille ayant des cases non assignée et leur assigner un nombre aléatoire
#      de sorte qu'il n'y ait pas 2 nombres identiques dans le meme carré 3x3
def fill(grid):
    filled = grid.copy()
    for bs in bigSquares:  # pour chaque carré 3x3
        possibilites = "123456789"
        for s in bs:
            possibilites = possibilites.replace(filled[s], '')  # on retire de nos possibilités les nombres deja présent dans le carré 3x3
        for s in bs:
            if filled[s] == '.' or filled[s] == '0':  # si on est sur un carré non-assigné
                randomnumber = random.choice(possibilites)  # on choisit un nombre
                filled[s] = randomnumber  # on l'assigne au carré
                possibilites = possibilites.replace(randomnumber, '')  # puis on retire ce nombre des possibilités

    return filled


# But : à partir de la grille non remplie, déterminé, à l'aide des cases vides, quels échangent peuvent-etre
#      fait dans un meme carré 3x3, sans changé le probleme (ie on ne veut pas echangé une des case connue, car
#      trouver une telle solution ne solutionne pas le bon sudoku), et ce sans avoir de répétition (par exemple,
#      échanger A1 et A2 est la meme chose que d'échangé A2 et A1)
def listSwapPossibles(grid):
    swaps = []
    for bs in bigSquares:  # pour chaque carré 3x3
        casesNonFixes = []
        for s in bs:
            if grid[s] == '.' or grid[s] == '0':
                casesNonFixes = casesNonFixes + [s]  # pour un carré 3x3, on fait la liste des cases pouvant être échangé
        for i in range(0, len(casesNonFixes)):
            for j in range(0, i):
                if i != j:
                    swaps = swaps + [(casesNonFixes[i], casesNonFixes[j])]  # pour chacune des ces cases, on trouve toutes les combinaisons d'échanges possibles
    return swaps


# But: pour une grille remplie donnée, calculé le nombre de conflits (sert
#     pour chaque carré, on regarde ses peers et on compte le nombre de peers ayant le meme chiffre
#     à la fin, on divise par 2 car chaque conflit a été compté 2 fois (par exemple si A3 et A8 sont en conflit, alors
#     ce conflit a été compté lorsque l'on a visité les peers de A3 et il a été compté une seconde fois lorsqu'on a visité
#     les peers de A8

def nombreConflits(grid):
    nb = 0  # le nombre total de conflit
    for s in squares:  # pour chaque carré unitaire
        for p in peers[s]:  # pour chaque peers de ce carré
            if grid[s] == grid[p]:
                nb += 1  # si ils sont en conflit, alors on incrémente le nombre de conflit total
    return nb / 2


# But : prendre une grille et un couple de cases, et interchange
#      le contenu des 2 cases de coupleASwap interchangé
def swap(grid, coupleASwap):
    temp = grid[coupleASwap[0]]
    grid[coupleASwap[0]] = grid[coupleASwap[1]]
    grid[coupleASwap[1]] = temp
    return grid

################ Constraint Propagation ################
# Fonction de Norvig
def assign(values, s, d):
    """Eliminate all the other values (except d) from values[s] and propagate.
    Return values, except return False if a contradiction is detected."""
    other_values = values[s].replace(d, '')
    if all(eliminate(values, s, d2) for d2 in other_values):
        return values
    else:
        return False


# Fonction de Norvig
def eliminate(values, s, d):
    """Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected."""
    if d not in values[s]:
        return values  ## Already eliminated
    values[s] = values[s].replace(d, '')
    ## (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(values[s]) == 0:
        return False  ## Contradiction: removed last value
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2) for s2 in peers[s]):
            return False
    ## (2) If a unit u is reduced to only one place for a value d, then put it there.
    for u in units[s]:
        dplaces = [s for s in u if d in values[s]]
        if len(dplaces) == 0:
            return False  ## Contradiction: no place for this value
        elif len(dplaces) == 1:
            # d can only be in one place in unit; assign it there
            if not assign(values, dplaces[0], d):
                return False
    return values

################ Display as 2-D grid ################

# Fonction de Norvig
def display(values):
    """Display these values as a 2-D grid."""
    width = 1 + max(len(values[s]) for s in squares)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        print ''.join(values[r + c].center(width) + ('|' if c in '36' else '')
                      for c in cols)
        if r in 'CF': print line
    print

################ Solving ################

# But : prend une grille lu du fichier/generée aléatoirement, puis appelle les bonnes fonctions
#      dans le bon ordre pour résoudre le sudoku,
#      retourne le sudoku solutionné si il a réussis a le résoudre, retourne False sinon
def solve(grid):
    originalGrid = grid_values(grid) #on traduit le string en grille
    if not est_valide(originalGrid):
        return False #la grille ne correspond pas a un sudoku solvable
    swaps = listSwapPossibles(originalGrid) #on genere les échanges possibles (pour les mutations)
    grids = []
    for i in range(0,POP):
        grids = grids + [fill(originalGrid)]#on genere la population initiale aleatoirement
    return genetique(grids, swaps) #algorithme genetique


#But : prendre la population et la liste des swaps possible (pour les mutatiions), et tenter de résoudre le sudoku
#      selon le principe de l'algorithme genetique
#      retourne la grille solvée, ou False si l'algorithme échoue
def genetique(grids, swaps):
    nbEtat = 0
    nbSwaps = 0
    bestDerniereGeneration = 10000 #grosse constante

    while(True):
        nbEtat += POP
        nbSwaps += POP
        resultHillClimbing = essayerDeSolveAll(grids, swaps)#on appel hillclimbing sur chaque sudoku
        nbEtat += resultHillClimbing[0]
        nbSwaps += resultHillClimbing[1]

        ##Les prochaines lignes vérifie si la on a résolut le sudoku, ou si la population est pire que la précédente
        ##en calculant les nombres de conflits
        ##note : meme si on utilise fitness comme non, ce n'est pas encore la vrai fitness
        totalFitness = 0
        fitness = []
        for g in grids:
            f = nombreConflits(g)
            fitness += [f]
        bestConflits = fitness[0]
        worstConflits = fitness[0]
        for i in fitness:
            if fitness[i] > worstConflits:
                worstConflits = fitness[i]
            if fitness[i] < bestConflits:
                bestConflits = fitness[i]

        if bestConflits == 0: #si on a un sudoku sans conflit, on le retourne
            s = min(nombreConflits(s) for s in grids)
            return (s, nbEtat, 0, nbSwaps) ## pas de conflit, donc deja résolut
        if bestConflits >= bestDerniereGeneration: #on ne s'est pas amélioré depuis la derniere generation -> failed
            return (False, nbEtat, bestDerniereGeneration, nbSwaps)
        bestDerniereGeneration = bestConflits

        #FONCTION DE FITNESS
        #on calcule la fitness à partir des nombres de conflits calculés plus haut
        for i in range(len(fitness)):
            fitness[i] = worstConflits - fitness[i] + 1 #notre fonction de fitness, les grilles avec beaucoup de conflits auront une faible fitness
                                            #et celles avec peu de conflits en auront beaucoup. Cette fonction est choisie de sorte que
                                            #la probabilité de choisir les plus fit est significativement plus grande que celle de choisir
                                            #les moins fit
            totalFitness += fitness[i]

        grids = genererNextGeneration(grids, swaps, fitness, totalFitness) #on genere la prochaine generation

#But:appeller hillclimbing sur chaque membre de la population
def essayerDeSolveAll(grids, swaps):
    toursTotal = 0
    swapsTotal = 0
    for g in grids:
        result = hillClimbing(g, swaps)
        g = result[0]
        toursTotal += result[1]
        swapsTotal += result[3]
    return (toursTotal, swapsTotal)

#But : prendre une grille remplie et la liste des swaps possible, et tenté de résoudre le sudoku
#      selon le principe de l'algorithme de hill climbing.
#      retourne la grille solutionné, ou False si l'algorithme échoue
def hillClimbing(grid, swaps):
    nbTours = 1   # Nb d'états explorés
    nbSwaps = 0
    conflitsAvant = nombreConflits(grid)  # le nombre de conflits dans la grille initialement
    while (True):
        onATrouveUnSwap = False
        if conflitsAvant == 0:
            return (grid, nbTours, 0, nbSwaps) ## pas de conflit, donc deja résolut
        for s in shuffled(swaps):
            conflitsApres = nombreConflits(swap(grid, s))
            nbSwaps += 1
            if conflitsApres < conflitsAvant:
                conflitsAvant = conflitsApres
                nbTours += 1
                onATrouveUnSwap = True
                break
            else:
                swap(grid, s)

        #comme on a pas résolut le sudoku, on cherche le meilleur swap possible
        if not onATrouveUnSwap: #on n'a pas trouvé de swap réduisant les conflits
            return (grid, nbTours, 0, nbSwaps) #on ne peu plus continuer, et on sait que l'on n'est pas à 0 conflit, donc le hillclimbing échoue

#but : generer une nouvelle generation de candidats. on chosit d'abord les 2 parents, puis ont les reproduit.
#      on repette jusqu'a avoir une population complete
def genererNextGeneration(grids, swaps, fitness, totalFitness):
    nextGeneration = []
    for i in range(POP):
        pere = trouverParent(grids, fitness, totalFitness)
        mere = trouverParent(grids, fitness, totalFitness)
        while(pere != mere): #bon ça looperait à l'infini si la population est inferieure a 2, mais on suppose que ça arrivera pas
            mere = trouverParent(grids, fitness, totalFitness)
        nextGeneration += [faireUnEnfant(pere, mere, swaps)]
    return nextGeneration

#la façon de choisir les parents se base sur le roulette wheel selection,
#voir https://en.wikipedia.org/wiki/Fitness_proportionate_selection
def trouverParent(grids, fitness, totalFitness):
    p = random.randint(1,totalFitness)  # devrait bien fonctionné car on sait que personne n'a un fitness de 0, donc le minimum
                                        # de totalFitness est POP
    acc = 0
    parent = None
    for j in range(len(fitness)):
        acc += fitness[j]
        if p <= acc:
            parent = grids[j]
            break
    return parent

#but : prendre deux parents et generer un nouveau sudoku (fonction de croisement)
def faireUnEnfant(pere, mere, swaps):
    child = pere.copy()
    for bs in bigSquares:
        if(random.randint(0,1) == 1):
            for u in bs:
                child[u] = mere[u]
    mutation(child, swaps)
    return child

#but : fonction de mutation, fait un swap selon un probabilité
def mutation(x, swaps):
    if random.randint(1,100) <= MUTATION_CHANCE:
        s = shuffled(swaps)[0]
        swap(x, s)


################ Utilities ################

# Fonction de Norvig
def some(seq):
    """Return some element of seq that is true."""
    for e in seq:
        if e: return e
    return False


# Fonction de Norvig
def from_file(filename):
    """Parse a file into a list of strings, line by line"""
    return file(filename).readlines()


# Fonction de Norvig
def shuffled(seq):
    """Return a randomly shuffled copy of the input sequence."""
    seq = list(seq)
    random.shuffle(seq)
    return seq

################ System test ################

import time, random


# Fonction de Norvig
def solve_all(grids, name='', showif=0.0):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""
    global solutionCounter
    solutionCounter = 0

    def time_solve(grid):
        global solutionCounter
        solutionCounter += 1
        start = time.clock()
        solvingResult = solve(grid)
        values = solvingResult[0]
        nbTours = solvingResult[1]
        bestConflits = solvingResult[2]
        nbSwaps = solvingResult[3]
        t = time.clock() - start
        print("Résultat : " + ("Échec" if values == False else "Succès") +
              "; Nombre d'étapes : " + str(nbTours) +
              "; Nombre d'échanges : " + str(nbSwaps) +
              "; Meilleur solution : " + str(bestConflits) + " conflits\n")
        f.write('\n' + str(solutionCounter) + (" Échec" if values == False else " Succès") +
                "  " + str(nbTours) +
                " " + str(nbSwaps) +
                "  " + str(bestConflits))
        ## Display puzzles that take long enough
        if showif is not None and t > showif:
            display(grid_values(grid))
            if values: display(values)
            print '(%.2f seconds)\n' % t
        return (t, solved(values))

    times, results = zip(*[time_solve(grid) for grid in grids])
    N = len(grids)
    if N > 1:
        print "Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)." % (sum(results), N, name, sum(times) / N, N / sum(times), max(times))
        f.write("\nSolved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs).\n" % (sum(results), N, name, sum(times) / N, N / sum(times), max(times)))


# Fonction de Norvig
def solved(values):
    """A puzzle is solved if each unit is a permutation of the digits 1 to 9."""

    def unitsolved(unit): return set(values[s] for s in unit) == set(digits)

    return values is not False and all(unitsolved(unit) for unit in unitlist)


# Fonction de Norvig
def random_puzzle(N=17):
    """Make a random puzzle with N or more assignments. Restart on contradictions.
    Note the resulting puzzle is not guaranteed to be solvable, but empirically
    about 99.8% of them are solvable. Some have multiple solutions."""
    values = dict((s, digits) for s in squares)
    for s in shuffled(squares):
        if not assign(values, s, random.choice(values[s])):
            break
        ds = [values[s] for s in squares if len(values[s]) == 1]
        if len(ds) >= N and len(set(ds)) >= 8:
            return ''.join(values[s] if len(values[s]) == 1 else '.' for s in squares)
    return random_puzzle(N)  ## Give up and make a new puzzle


### test gridds ###
grid1 = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'
grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
hard1 = '.....6....59.....82....8....45........3........6..3.54...325..6..................'
fhard = '000005080000601043000000000010500000000106000300000005530000061000000004000000000'

if __name__ == '__main__':
    test()
    f.write("\nSudoku #100 list")
    solve_all(from_file("100sudoku.txt"), "Sudoku #100 liste", None)
    # f.write("\nSudoku #1000 list")
    # solve_all(from_file("1000sudoku.txt"), "Sudoku #1000 list", None)
    f.write("\nSudoku #100 Random Sudoku")
    solve_all([random_puzzle() for _ in range(100)], "random", None)
    ##solve_all([fhard], "random", 100)
    f.close()

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
