from flask_wtf import Form
import wtforms
from wtforms import FieldList, FormField, SelectField, StringField, TextAreaField, HiddenField
from wtforms import validators
from . import models
from .voterlib import voterdb
import phonenumbers

class SignupForm(Form):
    name = StringField('Name', [validators.Required()])
    phone = StringField('Phone Number')
    voterid = StringField('Voter ID')
    place = HiddenField()

    def __init__(self, place=None, *a, **kw):
        Form.__init__(self, *a, **kw)
        self._place = place

    def validate_phone(self, field):
        phone = field.data
        if not phone:
            raise validators.ValidationError('This field is required.')
        if models.PendingMember.find(phone=phone) or models.Member.find(phone=phone):
            raise validators.ValidationError('This phone number is already used')

    def validate_voterid(self, field):
        if not self.voterid.data:
            if not self.place.data and (self._place and self._place.type.short_name not in ['PB', 'PX', 'LB', 'AC']):
                raise validators.ValidationError("You must provide either a valid voter ID or locality.")

        if self.voterid.data:
            voterid = self.voterid.data
            voterinfo = voterdb.get_voter(voterid=voterid, trynew=True)
            if not voterinfo:
                raise validators.ValidationError("Invalid Voter ID")

class AddVolunteerForm(Form):
    name = StringField('Name', [validators.Required()])
    email = StringField('Email Address')
    phone = StringField(label='Phone Number', validators=[validators.Required()], description="10 digits only")
    voterid = StringField('Voter ID')
    booth = SelectField('Polling Booth')

    def __init__(self, place, *a, **kw):
        Form.__init__(self, *a, **kw)
        self._place = place
        self._setup_booth_options()

    def _setup_booth_options(self):
        t = self._place.type.short_name
        if t == 'PB':
            self.booth.choices = [(self._place.key, self._place.name)]
            ## Anand: marking it as disabled is causing form validation error
            ## as the browser is not sending any data for this input.
            ## Commenting it out to avoid that issue.
            # self.booth.flags.disabled = True
        elif t in ['PX', 'LB', 'AC']:
            PB = models.PlaceType.get("PB")
            self.booth.choices = [(p.key, p.name) for p in self._place.get_places(PB)]
            self.booth.choices.insert(0, (self._place.key, "Not Sure"))
        else:
            self.booth.choices = [('', '')]
            ## Anand: marking it as disabled is causing form validation error
            ## as the browser is not sending any data for this input.
            ## Commenting it out to avoid that issue.
            # self.booth.flags.disabled = True

    def validate_phone(self, field):

        if len(field.data) != 10:
            raise validators.ValidationError('it should be 10 digit only')

        phone = field.data.strip()

        try:
            number = phonenumbers.parse(phone, "IN")
        except Exception:
            raise validators.ValidationError('Please enter number only')

        if phonenumbers.is_valid_number(number) == False:
            raise validators.ValidationError('Invalid Phone number')

        if models.Member.find(phone=phone):
            raise validators.ValidationError('This phone number is already used')

    def validate_email(self, field):
        email = field.data

        # email is optional
        if not email:
            return

        # if some value is provided, make sure it is a valid email address
        validate = validators.Email()
        validate(self, field)

        # make sure the email address is not already used
        if models.PendingMember.find(email=email) or models.Member.find(email=email):
            raise validators.ValidationError('This email address is already used')

    def validate_voterid(self, field):
        #SignupForm.validate_voterid(self, field)
        if self.voterid.data:
            voterid = self.voterid.data
            voterinfo = voterdb.get_voter(voterid=voterid)
            if voterinfo and not voterinfo.get_place().has_parent(self._place):
                raise validators.ValidationError("This voter ID doesn't belong to the current place.")


class SendMailForm(Form):
    people = SelectField('Send Email to',
                choices=[
                    ('self', 'Just Me (for testing)'),
                    ('volunteers', 'All Volunteers'),
                    ('contacts', 'All Contacts')
                ])
    subject = StringField('Subject', validators=[validators.Required()])
    message = TextAreaField("Message", validators=[validators.Required()])


class SendSMSForm(Form):
    people = SelectField('Send SMS to',
                choices=[
                    ('volunteers', 'All Volunteers'),
                    ('contacts', 'All Contacts')
                ])
    message = TextAreaField("Message", validators=[validators.Required()])

class UnsubscribeForm(Form):
    email = StringField('Email Address', [validators.Email()])
