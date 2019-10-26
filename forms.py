from wtforms import Form, StringField, DateField, IntegerField, Field
from wtforms.validators import DataRequired, Length, number_range, input_required, optional


class DataInputForm(Form):
    date = DateField('Date of Experiment')
    id = StringField('Experiment ID', validators=[
        DataRequired,
        Length(min=1, max=3)])
    initials = StringField('Your Initials', validators=[
        DataRequired,
        Length(min=2, max=4, message=u'Little short for your intiaials')])
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
    widesearch = Field('Would you like to broaden the search to include more extreme cycles?')
