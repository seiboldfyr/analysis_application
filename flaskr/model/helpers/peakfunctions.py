import numpy as np
from scipy.signal import peak_widths
from flask import current_app
from scipy.signal import _peak_finding
import matplotlib.pyplot as plt

from flaskr.model.helpers.calcfunctions import fit_poly_equation, get_expected_values, square


def get_peaks(self, well, derivativenumber, derivative, allpeaks) -> {}:
    timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
    
    # For gPCR experiments, we need to skip the first peak on the first dIndex (derivativenumber)
    num_of_peaks = 1 if derivativenumber == 1 and self.form.get('gPCR') == "True" else 2
    for i in range(num_of_peaks):
        if derivativenumber == 1:
            if i == 0:
                #first derivative largest peak
                #second phase
                inflectionnumber = 3
            else:
                #first derivative second largest derivative
                #first phase
                inflectionnumber = 1
        else:
            if i == 0:
                #second derivative largest peak
                #start of second phase
                timediff = [(timediff[t] + timediff[t + 1]) / 2 for t in range(len(timediff) - 1)]
                inflectionnumber = 2
            else:
                # second derivative largest trough
                # end of second phase
                inflectionnumber = 4

        maxpeak = list(np.where(derivative == max(derivative)))[0]

        # get the [width, width height, left_ips, right_ips] from the scipy peak width function
        widths = peak_widths(derivative, maxpeak)

        #handle peak property warning
        if widths[0] == 0 or int(widths[3][0]) - int(widths[2][0]) < 2:
            cut = 0
            tempderivative = derivative.copy()
            for idx, value in enumerate(tempderivative):
                if len(tempderivative) > value > tempderivative[idx + 1]:
                    cut = idx
                else:
                    tempderivative[:cut] = tempderivative[cut+1]
                    break
            maxpeak = list(np.where(tempderivative == max(tempderivative)))[0]
            widths = peak_widths(tempderivative, maxpeak)

        if widths[0] == 0:
            current_app.logger.error('Width finding error 1, dataset: %s' % self.dataset_id)
            break
        leftside = int(np.floor(widths[2][0]))
        rightside = np.min([int(np.ceil(widths[3][0])), len(derivative)-1])
        if rightside - leftside < 2:
            current_app.logger.error('Width finding error 2, dataset: %s' % self.dataset_id)
            break

        # fit a polynomial to the derivative
        polycoefs = fit_poly_equation(self.time[leftside:rightside],
                                      derivative[leftside:rightside])

        # Calculate the inflection point as the maximum of the fit polynomial
        # Calculate the expected RFU value at the inflection point by fitting a new polynomial to the original time/rfus
        # Collect all information into an inflection dictionary
        allpeaks[str(inflectionnumber)] = dict(inflection=-polycoefs[1] / (2 * polycoefs[0]),
                                               rfu=get_expected_values(self, well, -polycoefs[1] / (2 * polycoefs[0]),
                                                                       [leftside, rightside])[0],
                                               location=maxpeak)

        if derivativenumber == 2 and i == 0:
            inflectionnumber += 1
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
        for i in range(peakindex, len(data)-1):
            if data[i+1] <= trough:
                data[:i+1] = trough
                return -data
    return data[:peakindex]

