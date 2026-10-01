Initialize population with random timetables
Evaluate fitness of each timetable (check clashes, constraints)
While stopping condition not met:
    Select parents based on fitness
    Perform crossover to produce offspring
    Apply mutation to maintain diversity
    Evaluate fitness of new timetables
    Replace worst timetables with better ones
Output best timetable found
