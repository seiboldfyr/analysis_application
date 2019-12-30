import numpy as np


def square(data):
    return [i ** 2 for i in data]


def fit_poly_equation(timelist, observed):
    polynomial = 2
    coefs = np.polyfit(timelist, observed, polynomial)
    return coefs


def get_expected_values(self, well, x, borders) -> []:
    # Fits a 2nd degree polynomial to the original line
    # For estimating the 'y' of a given 'x'
    # x can be a list or a single element
    polynomialcoefs = fit_poly_equation(self.time[borders[0]:borders[1]],
                                        well.get_rfus()[borders[0]:borders[1]])
    if isinstance(x, float):
        x = [x]
    x2 = square(x)
    ax2 = [polynomialcoefs[0] * x for x in x2]
    bx = [polynomialcoefs[1] * x for x in x]
    prediction = [(a + b + polynomialcoefs[2]) for (a, b) in zip(ax2, bx)]
    return prediction


def get_percent_difference(self, inflections):
    relativeDifference = [abs(a - b) / ((a + b) / 2) for a, b in zip(inflections, self.control)]
    return [element * 100 for element in relativeDifference]


def get_derivatives(well) -> []:
    # Returns the first and second derivatives in a dictionary
    derivative = {1: smooth(np.gradient(well.get_rfus()))}
    derivative[2] = np.gradient(derivative[1])
    return derivative


def smooth(a):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    windowsize = 11
    out0 = np.convolve(a, np.ones(windowsize, dtype=int), 'valid') / windowsize
    r = np.arange(1, windowsize - 1, 2)
    start = np.cumsum(a[:windowsize - 1])[::2] / r
    stop = (np.cumsum(a[:-windowsize:-1])[::2] / r)[::-1]
    return np.concatenate((start, out0, stop))
