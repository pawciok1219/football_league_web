from django.forms import ModelForm
from django.contrib.auth.models import User,Group
from .models import Team,Player, Match, StatsPlayerMatch
from django.contrib.auth.forms import UserCreationForm
from captcha.fields import ReCaptchaField
from django import forms


class PlayerForm(ModelForm):
    class Meta:
        model = Player
        fields = ['firstName', 'secondName', 'pesel', 'age', 'position', 'statusHealth']


class PlayerEditForm(ModelForm):
    class Meta:
        model = Player
        fields = ['age', 'position', 'statusHealth']


class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'date_creation', 'logo']


class UserForm(UserCreationForm):
    group_name = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)
    captcha = ReCaptchaField(error_messages={'required': 'Captcha jest wymagana.'})

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'group_name', 'captcha']


class Protocol(ModelForm):
    class Meta:
        model = StatsPlayerMatch
        fields = ['numberOfGoals', 'numberOfYellowCard']


class MatchForm(ModelForm):
    class Meta:
        model = Match
        fields = ['Home', 'Guest', 'startDate', 'idQueue']