from wtforms import Form, StringField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, number_range, input_required, optional


def calculatecyclelength(totaltime, totaldata):
    return totaltime/totaldata


class DataInputForm(Form):
    """Data Input Form."""

    date = DateField('Date of Experiment')
    id = StringField('Experiment ID', validators=[
        DataRequired,
        Length(min=1, max=3)
    ])
    initials = StringField('Your Initials', validators=[
        DataRequired,
        Length(min=2, max=4, message=u'Little short for your intiaials')
    ])
    cyclelength = StringField('Seconds per Cycle')
    cutlength = StringField('Fluorescence Error Cut Time')
    length = IntegerField('Experiment Length (Minutes)', validators=[
        number_range(min=0, message='Please enter a nonzero value.')
    ])
    totaldata = IntegerField('Data points collected for the experiment', validators=[
        number_range(min=0, message='Please enter a nonzero value.')
    ])
    submit = SubmitField('Submit')



