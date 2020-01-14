import re
from flask import flash

from flaskr.database.dataset_models.repository import Repository


def build_swap_inputs(self):
    for item in self.request.form.keys():
        if item.startswith('Swap From'):
            self.swaps[self.request.form[item]] = self.request.form['Swap To ' + str(item[-1])]
        if item.startswith('Bidirectional Swap') == True:
            self.swaps[self.request.form['Swap To ' + str(item[-1])]] = self.request.form['Swap From ' + str(item[-1])]


def build_group_inputs(self):
    for item in self.request.form.keys():
        if item.startswith('Group'):
            if self.groupings.get(str(item[-1])) is None:    #TODO: see the (*) TODO item in processor.py, this is source of error
                self.groupings[str(item[-1])] = {}
            self.groupings[item[-1]][item[:-2]] = self.request.form[item]


def get_collection(self):
    dataset_repository = Repository()
    dataset = dataset_repository.get_by_id(self.dataset_id)
    return dataset.get_well_collection()


def get_concentrations(string):
    if string.endswith('fM'):
        return float(re.match(r'^\d+', string).group(0)) / 1000
    elif string.endswith('pM'):
        return float(re.match(r'^\d+', string).group(0))
    elif string.endswith('nM'):
        return float(re.match(r'^\d+', string).group(0)) * 1000
    else:
        return 0


def add_custom_group_label(self, well):
    originallabel = well.get_label().split('_')
    well['label'] = '_'.join([item for item in originallabel[:2]])
    if self.groupings.get(str(well.get_group())):
        well['label'] = well.get_label() + '_' + self.groupings[str(well.get_group())]['Group Label']
    well['label'] += '_' + str(well.get_group())
    return well


def edit_RFUs(self, originwell, cut):
    originwell.edit_labels(dict(RFUs=originwell.get_rfus()[cut:]))
    self.measurement_manager.update(originwell)


def swap_wells(self, originwell):
    for destwell in get_collection(self):
        if destwell.get_excelheader() == self.swaps[originwell.get_excelheader()]:
            originwell.edit_labels(dict(group=destwell.get_group(),
                                        sample=destwell.get_sample(),
                                        triplicate=destwell.get_triplicate(),
                                        label=destwell.get_label(),
                                        RFUs=destwell.get_rfus()))
            self.measurement_manager.update(originwell)


def validate_errors(self):
    for well in self.request.form['errorwells'].split(', '):
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