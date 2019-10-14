from wtforms import Form, StringField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Length, number_range, input_required, optional


class DataInputForm(Form):
    """Data Input Form."""

    date = DateField('Date of Experiment')
    id = StringField('Experiment ID', validators=[
        DataRequired,
        Length(min=1, max=3)])
    initials = StringField('Your Initials', validators=[
        DataRequired,
        Length(min=2, max=4, message=u'Little short for your intiaials')])
    customlabel = StringField('Custom Label Addition')
    cutlength = StringField('Fluorescence Error Cut Time')
    folder = StringField('Folder Path')

    submit = SubmitField('Submit')



