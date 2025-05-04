import ape_com as ape
import slm_com as slm
import data_processing as data
import numpy as np
import pandas
import time
import os

def init(N, pd, lb, ub):
    '''
    Initialize the flock
    :param N: Flock (population) size
    :param pd: problem dimension
    :param lb: lower bound
    :param ub: upper bound
    :param path: path to file with masks
    :return: population
    '''
    '''
    dir_path = os.getcwd()
    path = f'{dir_path}/random_masks/{pd}_stripes_rand_masks.csv'
    df = pd.read_csv(path)
    pop = df.loc[:N]
    pop = pop.to_numpy()
    return pop
    '''
    return init_random(N, pd, lb, ub)
    #return fetch_init_masks(pd, N)


def fetch_init_masks(pd, population_size):
    '''

    :param pd: problem dimension (number of stripes)
    :param population_size:
    :return:
    '''
    filename = f'{pd}_stripes_rand_masks.csv'
    folderpath = os.path.join(os.getcwd(), 'random_masks')
    filepath = os.path.join(folderpath, filename)

    df = pandas.read_csv(filepath, delimiter=';')
    masks = df.to_numpy()
    return masks[:population_size, :]

def init_random(N, pd, lb, ub):
    '''
    Initialize the flock
    :param N: Flock (population) size
    :param pd: problem dimension
    :param lb: lower bound
    :param ub: upper bound
    :return: population
    '''

    pop = np.random.randint(low=lb, high=ub, size=(N, pd))
    return pop

def objective(pulseCheck, scan_range, vec, pd):
    '''
    Calculates the fitness of the bird
    :param pulseCheck:
    :param scan_range:
    :param vec: vector containing the position of the bird
    :param pd: problem dimension
    :return: fitness
    '''

    int_positions = vec.astype(int)
    stripe_width = int(slm.slm_w/pd)
    mask = data.vec_to_mask(int_positions, stripe_width)
    slm.send_mask(mask)
    time.sleep(1)
    delay, acf = ape.read_acf(pulseCheck)
    fwhm, fit, fitness, acf_area = data.calc_pulse_qual(acf, delay, scan_range)
     return fitness

def get_acf(pulseCheck, scan_range, vec, pd):
    '''
    Calculates the fitness of the bird but returns the autocorrelation and fit also
    :param pulseCheck:
    :param scan_range:
    :param vec:
    :param pd:
    :return:
    '''

    int_positions = vec.astype(int)
    stripe_width = int(slm.slm_w / pd)
    mask = data.vec_to_mask(int_positions, stripe_width)
    slm.send_mask(mask)
    time.sleep(1)
    delay, acf = ape.read_acf(pulseCheck)
    fwhm, fit, fitness, acf_area = data.calc_pulse_qual(acf, delay, scan_range)
    return fitness, delay, acf, fit

def crow_search(pd, N, AP, fl, iter, lb, ub, pulseCheck, scan_range):
    '''
    Crow search algorithm
    :param pd: problem dimension -> number of stripes
    :param N: Flock (population) size
    :param AP: Awareness probability
    :param fl: flight length
    :param iter: max number of iterations
    :param lb: lower bound
    :param ub: upper bound
    :return: fitness list, best mask
    '''

    # x - crows positions
    # mem - memory storing the hiding-food locations
    # ft - fitness array, stores the fitness of the hiding-food locations
    # ft_mem - memory storing fitness values of the positions in memory

    x = init(N, pd, lb, ub)     #initial population
    fitness_list = []       #fitness list
    #ft = (objective(pulseCheck, scan_range, v, pd) for v in x)
    ft = []
    for v in x:
        ft.append(objective(pulseCheck, scan_range, v, pd)) # wypełnienie fitness

    #initialize the memory
    mem=x   # first hiding-food locations are
    fit_mem = ft    # first fitness memory

    for i in range(iter):
        #num = np.random.randint(low=0, high=N, size = N) #Generation of random candidate crows for following (chasing)
        #xnew = np.zeros((N, pd))

        #for crow_idx in range(x.shape[0]-1):
        for crow_i in range(N):
            # Pick a crow to follow
            crow_j = np.random.randint(low=0, high=N)  # Generation of random candidate crows for following (chasing)
            rand_num = np.random.rand() # Generate a random number between 0 and 1 for awareness probability
            if rand_num > AP:
                # crow i chases crow j
                #xnew[crow_idx, :] = x[crow_idx, :] + fl*rand_num*(mem[num[crow_idx], :]-x[crow_idx, :]) # Generation of a new position for crow i (state 1)
                #xnew[crow_i, :] = x[crow_i, :] + fl * rand_num * (mem[num[crow_i], :] - x[crow_i, :])  # Generation of a new position for crow i (state 1)
                x[crow_i, :] = x[crow_i, :] + fl * rand_num * (mem[crow_j, :] - x[crow_i, :])  # Generation of a new position for crow i (state 1)
                # tu powinno być chyba sprawdzenie czy maska jest w bounds?
            else:
                # crow j is aware, goes to random position
                x[crow_i, :] = np.random.randint(lb, ub, pd)

        #xn = xnew
        #ft = (objective(pulseCheck, scan_range, v, pd) for v in xn)  # Function for fitness evaluation of new solutions
        ft = [] #fitness values placeholder
        for position in x:
            ft.append(objective(pulseCheck, scan_range, position, pd)) #check the fitness

        for crow in range(N):  # Update position and memory
            if np.all(x[crow, :] >= lb) and np.all(x[crow, :] <= ub):   # Check if within bounds
                #x[j, :] = xnew[j,:] #xnew[i, :]    # Update position
                if ft[crow] < fit_mem[crow]:
                    mem[crow, :] = x[crow, :]
                    fit_mem[crow] = ft[crow]
            else:
                print(f'not within bounds')

        min_fit = np.min(fit_mem)
        print(f'The best fitness, iteration {i}: {min_fit}')
        min_fit_idx = np.argmin(fit_mem)
        fitness_list.append(min_fit)
        print(f'Best mask so far, iteration {i}: {mem[min_fit_idx]}')
        print(f'Fitness measured rn with the best mask so far: {objective(pulseCheck, scan_range, mem[min_fit_idx], pd)}')

    #ngbest = np.where(fit_mem == np.min(fit_mem))[0] #global best
    global_best = np.min(fit_mem)
    print(f'The best fitness, overall: {global_best}')
    #g_best = mem[ngbest[0], :]  # global best position (mask)
    min_fit_idx = np.argmin(fit_mem)
    global_best_position = mem[min_fit_idx]
    print(f'Best mask: [{global_best_position}]')
    print(f'Fitness measured rn with the best mask: {objective(pulseCheck, scan_range, mem[min_fit_idx], pd)}')
    #return [g_best, ngbest, fitness_list]
    return [global_best, global_best_position, fitness_list]