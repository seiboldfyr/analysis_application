import numpy as np
from scipy.signal import peak_widths
from flaskr.model.helpers.calcfunctions import fit_poly_equation, get_expected_values


def get_peaks(self, well, derivativenumber, derivative, allpeaks) -> {}:
    timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
    derivative = derivative[5:]
    inflectionnumber = 1
    for i in range(2):
        if derivativenumber == 2 and i == 0:
            timediff = [(timediff[t] + timediff[t + 1]) / 2 for t in range(len(timediff) - 1)]
            inflectionnumber += 2
        maxpeak = list(np.where(derivative == max(derivative)))[0]
        widths = peak_widths(derivative, maxpeak)
        if widths[0] == 0:
            break
        leftside = int(widths[2][0])
        rightside = int(np.min([widths[3][0], len(derivative)-1]))
        if rightside - leftside < 2:
            break
        polycoefs = fit_poly_equation(timediff[leftside:rightside],
                                      derivative[leftside:rightside])

        allpeaks[str(inflectionnumber+i)] = dict(inflection=-polycoefs[1] / (2 * polycoefs[0]),
                                                 rfu=get_expected_values(self, well, maxpeak, [leftside, rightside])[0])

        if derivativenumber == 2 and i == 0:
            derivative = remove_peak(derivative, maxpeak[0], getnegativedata=True)
        else:
            derivative = remove_peak(derivative, maxpeak[0])
    return allpeaks


def remove_peak(data, peakindex, getnegativedata=False):
    # Finds the lowest trough that occurs immediately before or after the peak
    # replaces the peak with the trough value
    trough = data[peakindex]
    for i in range(peakindex, 1, -1):
        if data[i-1] <= data[i]:
            trough = data[i-1]
        else:
            data[i:peakindex] = trough
            break
    if getnegativedata:
        for i in range(peakindex, len(data)):
            if data[i+1] <= trough:
                data[:i+1] = trough
                return -data
    return data[:peakindex]

