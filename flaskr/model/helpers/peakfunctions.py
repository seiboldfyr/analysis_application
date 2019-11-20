import numpy as np
from scipy.signal import find_peaks
from flaskr.model.helpers.calcfunctions import get_max_width


def get_peaks(dindex, derivative) -> []:
    if dindex == 2:  # flip to find the negative peak
        derivative = -derivative
    for proms in range(20, 5, -1):
        for width in range(15, 5, -1):
            peaks, properties = find_peaks(abs(derivative), prominence=proms, width=width)
            if len(peaks) == 2:
                return get_peak_borders(peaks, properties, len(derivative))
    # search more extremes if it doesn't work
    for proms in range(10,1,-1): # (50,10,-1):
        for width in range(5,1,-1): # (8,1,-1):
            peaks, properties = find_peaks(abs(derivative), prominence=proms, width=width)
            if len(peaks) == 2:
                return get_peak_borders(peaks, properties, len(derivative))
    # TODO: what if more than two peaks are found?
    return ['Error finding peaks', 0, 0]


def get_peak_borders(peaks, properties, maxlength):
    widths = get_max_width(properties["widths"])
    start = [np.maximum(int(peakstart - width), 1) for peakstart, width in zip(peaks, widths)]
    end = [np.minimum(int(peakend + width), maxlength) for peakend, width in zip(peaks, widths)]
    return [peaks, start, end]