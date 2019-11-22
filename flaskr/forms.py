from wtforms import Form, StringField, DateField, IntegerField, Field
from wtforms.validators import DataRequired, Length, number_range, input_required, optional


class DataInputForm(Form):
    date = DateField('Date of Experiment')
    id = StringField('Experiment ID')
    initials = StringField('Your Initials')
    customlabel = StringField('Custom Label Addition')
    cutlength = StringField('Fluorescence Error Cut Time')


class ExperimentInputForm(Form):
    customlabel = StringField('Custom Label Addition')
    cutlength = StringField('Fluorescence Error Cut Time')
    groupnum = IntegerField('Number of groups')
    grouptitle = StringField('Group Number')
    grouplabel = StringField('Custom label')
    groupwells = IntegerField('Number of wells')
    groupsamples = IntegerField('Number of samples')
    errorwells = StringField('Any wells with known errors')
    swaplabel = StringField('Swapping well positions - how many swaps do you want to make? ')
    labelfrom = StringField('Swap well from: ')
    labelto = StringField('Swap well to: ')
    widesearch = Field('Would you like to broaden the search to include more extreme cycles?')
