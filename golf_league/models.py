from django.db import models

# Create your models here.
class LeagueSeason(models.Model):
    name = models.CharField(max_length=200,null=True, blank=True)

    def __str__(self):
        return "FSGS " + self.name

class LeagueEvent(models.Model):
    leagueseason = models.ForeignKey(LeagueSeason, on_delete=models.RESTRICT)
    event_date = models.DateField(null=True, blank=True)
    event_golf_course = models.CharField(max_length=200,null=True, blank=True)
    event_status = models.CharField(max_length=1,null=True, choices=[("N","Not Started"),("C","Completed"),("R","Rainout")],default="N")

    def __str__(self):
        """String for representing the Model object."""
        return str(self.event_date)

class LeaguePlayer(models.Model):
    first_name = models.CharField(max_length=200,null=True, blank=True)
    last_name = models.CharField(max_length=200,null=True, blank=True)
    gender = models.CharField(max_length=1,choices=[("M","Male"),("F","Female")])

    def __str__(self):
        """String for representing the Model object."""
        return self.first_name + " " +self.last_name

class Handicap(models.Model):
    golfer = models.ForeignKey(LeaguePlayer, on_delete=models.CASCADE, null=True)
    handicap = models.DecimalField(max_digits=3,decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)
    effective_at = models.DateField()
    update_user = models.CharField(max_length=200,null=True, blank=True)
    update_golf_round = models.OneToOneField('PlayedRound', on_delete=models.SET_NULL, null=True, blank=True)
    update_comment = models.CharField(max_length=200,null=True, blank=True)

    def __str__(self):
        """String for representing the Model object."""
        return str(self.handicap)

class EventPlayer(models.Model):
    golfer = models.ForeignKey(LeaguePlayer,on_delete=models.RESTRICT)
    league_event = models.ForeignKey(LeagueEvent, on_delete=models.RESTRICT, null=False)
    round_handicap = models.OneToOneField(Handicap,on_delete=models.SET_NULL, null=True, blank=True)
    new_player_flag = models.CharField(max_length=1,choices=[("Y","New Player"),("N","Existing Player")])
    played_round = models.OneToOneField('PlayedRound', on_delete=models.SET_NULL,null=True, blank=True)
    #tee_time12234f g6gv7vh7hj9h

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.golfer.first_name + " " +self.golfer.last_name}'
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['golfer', 'league_event'], name='unique_player')]
        
class PlayedRound(models.Model):
    event_player = models.OneToOneField(EventPlayer, on_delete=models.CASCADE)
    gross_score = models.IntegerField() 
    net_score = models.IntegerField() 
    net_rel_par = models.IntegerField()
    coconut_pts = models.IntegerField(null=True, blank=True)
    handicap_adjustment = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String for representing the Model object."""
        return str(self.event_player.golfer.first_name)