import numpy as np
from scipy.integrate import trapz, trapezoid
import datetime
import os
import matplotlib.pyplot as plt

def vec_to_mask(vec, stripe_width):
    new_vec = []

    for element in vec:
        temp = np.full(stripe_width, element)
        new_vec = np.concatenate((new_vec, temp))
        mask = [new_vec for i in range(1200)]
        mask = np.array(mask, dtype=np.int16)

    return mask

def vec_to_half_mask(vec, stripe_width):
    new_vec = []
    black_vec = np.full(int(1920 / 4), 0)

    for element in vec:
        temp = np.full(stripe_width, element)
        new_vec = np.concatenate((new_vec, temp))

    new_vec = np.concatenate((black_vec, new_vec, black_vec))
    mask = [new_vec for i in range(1200)]
    mask = np.array(mask, dtype=np.int16)

    return mask

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def sech_squared(x, fwhm):
    fwhm/=1000 #change to ps
    x_parameter = fwhm / (2 * np.log(2))
    return (1 / np.cosh(x / x_parameter)) ** 2

def normalize_delay(delay, acf):
    delayn = delay
    idx = np.argmax(acf)
    offset = delay[idx]
    for i in range(len(delayn)):
        delayn[i]-=offset

    return delayn

def calc_pulse_qual(acf, delay, scan_range):
    # normalize the ACF

    delay = normalize_delay(delay, acf)

    normalized = (acf - np.min(acf)) / (np.max(acf) - np.min(acf))

    # find the index of peak value
    i = np.where(normalized==1)
    i = i[0][0]

    arr_left = normalized[0:i]
    arr_right = normalized[i:]

    # find the half values
    i_left = find_nearest(np.flip(arr_left), 0.5)
    i_right = find_nearest(arr_right, 0.5)

    left_delay = np.flip(delay[0:i])
    right_delay = delay[i:]
    fwhm = abs(right_delay[i_right] - left_delay[i_left]) * 1000

    step = scan_range / len(normalized)
    start = -1 * scan_range / 2
    stop = scan_range / 2

    # calculate the integral of ACF
    area = trapezoid(normalized, dx = step)

    # calculate the sech^2 fit
    fit = (1 / (np.cosh((1762 / fwhm)*np.array(delay)))) ** 2

    # calculate the new coefficient
    # integral of the fit
    area_fit = trapezoid(fit, dx=step)
    pulse_qual = fwhm * ((1 + abs(1 - (area_fit / area)))**2)

    return fwhm, fit, pulse_qual, area

def save_to_csv(parent_dir, genes, population_size, n_iter, AP, fl, fitness_list, best, delay, acf, fit):
    now = datetime.datetime.now()
    date = now.strftime(("%d%m%y_%H%M%S"))

    dir_name = f'cs_optim_{date}_{genes}_stripes_{population_size}_pop_{n_iter}_iter_{AP}_ap_{fl}_fl'
    path = os.path.join(parent_dir, dir_name)
    os.mkdir(path)

    np.savetxt(f'{path}/fitness_list.csv', fitness_list, delimiter=';')
    np.savetxt(f'{path}/vec.csv', best, delimiter=';')
    np.savetxt(f'{path}/delay.csv', delay, delimiter=';')
    np.savetxt(f'{path}/acf.csv', acf, delimiter=';')
    np.savetxt(f'{path}/fit.csv', fit, delimiter=';')

def plot_fitness(fitness, title):
    plt.plot(fitness)
    plt.xlabel('Iterations')
    plt.ylabel('Fitness')
    plt.title(title)
    plt.show()

