
from django import forms
from .models import EventPlayer, LeaguePlayer, Handicap, PlayedRound

# Create the form class.
class UpdateEventPlayerForm(forms.ModelForm):
    class Meta:
        model =  Handicap
        fields = ['handicap', 'update_comment']

class CreateEventPlayerForm(forms.ModelForm):
    league_player_id = forms.ModelChoiceField(LeaguePlayer.objects.all().order_by('first_name'))

    class Meta:
        model =  EventPlayer
        fields = ['league_player_id']

class CreateLeaguePlayerForm(forms.ModelForm):
    handicap = forms.FloatField(required = False)
    class Meta:
        model =  LeaguePlayer
        fields = ['first_name', 'last_name', 'gender']

class UploadScoresForm(forms.Form):
    results_file = forms.FileField()

class CreatePlayedRoundForm(forms.ModelForm):
    class Meta:
        model =  PlayedRound
        fields = ['gross_score']
