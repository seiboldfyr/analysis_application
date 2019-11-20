

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