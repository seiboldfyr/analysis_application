import re
from flask import flash, current_app

from flaskr.database.dataset_models.repository import Repository


def build_swap_inputs(self):
    for item in self.form.keys():
        if item.startswith('Swap From'):
            self.swaps[self.form[item]] = self.form['Swap To ' + str(item[-1])]
        if item.startswith('Bidirectional Swap') == True:
            self.swaps[self.form['Swap To ' + str(item[-1])]] = self.form['Swap From ' + str(item[-1])]


def build_group_inputs(self):
    for item in self.form.keys():
        if item.startswith('Group'):
            if self.groupings.get(str(item[-1])) is None:    #TODO: this doesn't account for groups 10 or higher
                self.groupings[str(item[-1])] = {}
            self.groupings[item[-1]][item[:-2]] = self.form[item]


def get_collection(self):
    dataset_repository = Repository()
    dataset = dataset_repository.get_by_id(self.dataset_id)
    return dataset.get_well_collection()


def get_existing_metadata(self):
    dataset_repository = Repository()
    model = dataset_repository.get_by_id(self.dataset_id)
    self.form = dict(form=dict())
    self.form = model.get_metadata()


def update_metadata(self):
    dataset_repository = Repository()
    model = dataset_repository.get_by_id(self.dataset_id)
    model['metadata'] = self.form
    dataset_repository.save(model)


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
        grouplim = int(self.groupings[g]['Group Wells'])
        lowlim = 0
        if g != '1':
            lowlim = sum([int(self.groupings[str(i)]['Group Wells']) for i in range(1,int(g))])
            grouplim = lowlim + int(self.groupings[g]['Group Wells'])
        if lowlim <= wellIndex < grouplim:
            originallabel = well.get_label().split('_')
            well['label'] = '_'.join([item for item in originallabel[:2]])
            if self.groupings.get(g):
                well['label'] = well.get_label() + '_' + self.groupings[g]['Group Label']       # TODO: Figure out how to redefine triplicate or sample
            well['label'] += '_' + g
            well['group'] = int(g)
    return well


def edit_RFUs(self, originwell, cut):
    originwell.edit_labels(dict(RFUs=originwell.get_rfus()[cut:]))
    self.measurement_manager.update(originwell)


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
                                            label=self.tempswaps[tempwell]['label'],
                                            RFUs=self.tempswaps[tempwell]['RFUs']))
                return originwell

    # search all wells until the destination well is found
    for destwell in get_collection(self):
        if destwell.get_excelheader() == self.swaps[originwell.get_excelheader()]:
            originwell.edit_labels(dict(group=destwell.get_group(),
                                        sample=destwell.get_sample(),
                                        triplicate=destwell.get_triplicate(),
                                        label=destwell.get_label(),
                                        RFUs=destwell.get_rfus()))
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