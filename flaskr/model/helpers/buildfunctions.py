import re
from flask import flash, current_app

from flaskr.model.helpers.importfunctions import get_collection


def build_swap_inputs(self):
    for item in self.form.keys():
        if item.startswith('swap'):
            swapfrom = self.form[item].split(' ')[0]
            swapto = self.form[item].split(' ')[1]
            if len(self.form[item].split(' ')) > 2:
                self.swaps[swapto] = swapfrom
            self.swaps[swapfrom] = swapto


def build_group_inputs(self):
    for item in self.form.keys():
        if item.startswith('group'):
            groupnum = get_digit_ending(item)
            if self.groupings.get(groupnum) is None:
                self.groupings[groupnum] = {}
            groupdata = self.form[item].split(' ')
            self.groupings[groupnum] = dict(Label=groupdata[0],
                                            Wells=groupdata[1],
                                            Sample=groupdata[2],
                                            Controls=groupdata[3])


def get_digit_ending(string):
    digit = 0
    if string[-2].isdigit():
        digit = str(string[-2:])
    else:
        digit = str(string[-1])
    return digit

def get_concentrations(string):
    if string.endswith('fM'):
        return float(re.match(r'^\d+', string).group(0)) / 1000
    elif string.endswith('pM'):
        return float(re.match(r'^\d+', string).group(0))
    elif string.endswith('nM'):
        return float(re.match(r'^\d+', string).group(0)) * 1000
    else:
        return 0


def add_custom_group_label(self, well, wellIndex):
    for g in self.groupings.keys():
        grouplim = int(self.groupings[g]['Wells'])
        lowlim = 0
        if g != '1':
            lowlim = sum([int(self.groupings[str(i)]['Wells']) for i in range(1,int(g))])
            grouplim = lowlim + int(self.groupings[g]['Wells'])
        if lowlim <= wellIndex < grouplim:
            originallabel = well.get_label().split('_')
            well['label'] = '_'.join([item for item in originallabel[:2]])
            if self.groupings.get(g):
                well['label'] = well.get_label() + '_' + self.groupings[g]['Label']       # TODO: Figure out how to redefine triplicate or sample
            well['label'] += '_' + g
            well['group'] = int(g)
    return well


def save_temporary_swap(self, originwell):
    self.tempswaps[originwell.get_excelheader()] = dict(group=originwell.get_group(),
                                                        sample=originwell.get_sample(),
                                                        triplicate=originwell.get_triplicate(),
                                                        label=originwell.get_label(),
                                                        RFUs=originwell.get_rfus())


def swap_wells(self, originwell): # replaces origin well info with destination well info
    # Save well info if it shows up as a destination well elsewhere
    if originwell.get_excelheader() in self.swaps.values():
        save_temporary_swap(self, originwell)

    # Check the temporary wells first
    if self.tempswaps is not None:
        for tempwell in self.tempswaps.keys():
            if self.swaps[originwell.get_excelheader()] == tempwell:
                originwell.edit_labels(dict(group=self.tempswaps[tempwell]['group'],
                                            sample=self.tempswaps[tempwell]['sample'],
                                            triplicate=self.tempswaps[tempwell]['triplicate'],
                                            label=self.tempswaps[tempwell]['label']))
                return originwell

    # search all wells until the destination well is found
    for destwell in get_collection(self):
        if destwell.get_excelheader() == self.swaps[originwell.get_excelheader()]:
            originwell.edit_labels(dict(group=destwell.get_group(),
                                        sample=destwell.get_sample(),
                                        triplicate=destwell.get_triplicate(),
                                        label=destwell.get_label()))
            return originwell

    flash('Swap could not be completed for well: %s' % originwell.get_excelheader(), 'error')
    current_app.logger.error('A swap could not be completed, dataset: %s' % self.dataset_id)
    return originwell


def validate_errors(self):
    if not self.form.get('errorwells'):
        return self.errorwells

    for well in self.form['errorwells'].split(', '):
        if len(well) == 3:
            add_errorwell(self, well)
        else:
            for item in well.split(','):
                if not item:
                    continue
                elif len(item) == 3:
                    add_errorwell(self, item)
                else:
                    flash('Formatting error for  %s' % str(item), 'error')
    return self.errorwells


def add_errorwell(self, iter):
    self.errorwells.append(re.match(r'([A-Z])+\d\d', str(iter)).group(0))