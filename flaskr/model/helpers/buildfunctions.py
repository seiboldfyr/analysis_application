import re

from flaskr.database.dataset_models.repository import Repository


def build_swap_inputs(self):
    for item in self.request.form.keys():
        if item.startswith('Swap From'):
            self.swaps[self.request.form[item]] = self.request.form['Swap To ' + str(item[-1])]


def build_group_inputs(self):
    for item in self.request.form.keys():
        if item.startswith('Group'):
            if self.groupings.get(str(item[-1])) is None:
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
