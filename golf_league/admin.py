from django.contrib import admin
from .models import LeagueSeason, LeagueEvent, Handicap, LeaguePlayer, EventPlayer, PlayedRound

# Register your models here.
#admin.site.register(Handicap)
#admin.site.register(LeagueEvent)
#admin.site.register(EventPlayer)
#admin.site.register(PlayedRound)
#admin.site.register(LeagueSeason)
#admin.site.register(LeaguePlayer)


class EventPlayerAdmin(admin.ModelAdmin):
    list_display = ('golfer','league_event','event_league_season', 'event_date')
    ordering = ['league_event']
    readonly_fields=('round_handicap',)
    def event_date(self, obj):
        return obj.league_event.event_date
    def event_league_season(self, obj):
        return obj.league_event.leagueseason
   
admin.site.register(EventPlayer, EventPlayerAdmin)

class PlayedRoundAdmin(admin.ModelAdmin):
    list_display = ('event_player','get_league_event','get_new_player_flag', 'get_round_handicap','gross_score','net_score','net_rel_par', "coconut_pts")
    ordering = ['created_at']
    def get_round_handicap(self, obj):
        return obj.event_player.round_handicap
    get_round_handicap.short_description = 'Round Handicap'
    def get_league_event(self, obj):
        return obj.event_player.league_event
    def get_new_player_flag(self, obj):
        return obj.event_player.new_player_flag
    get_new_player_flag.short_description = 'New Player Flag'
    
admin.site.register(PlayedRound, PlayedRoundAdmin)

class LeagueEventInline(admin.TabularInline):
    model = LeagueEvent
    extra = 0
class LeagueSeasonAdmin(admin.ModelAdmin):
    inlines = [LeagueEventInline]
admin.site.register(LeagueSeason, LeagueSeasonAdmin)

class EventPlayersInline(admin.TabularInline):
    model = EventPlayer
    extra = 0
class LeagueEventAdmin(admin.ModelAdmin):
    inlines = [EventPlayersInline]
    list_display = ('event_date','leagueseason','event_golf_course', 'event_status')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.event_status == 'R':
            eventplayers_to_delete = EventPlayer.objects.filter(league_event=obj).delete()

admin.site.register(LeagueEvent, LeagueEventAdmin)


class LeaguePlayerAdmin(admin.ModelAdmin):
    list_display = ('__str__','first_name','last_name','gender')
    ordering = ["first_name"]
admin.site.register(LeaguePlayer,LeaguePlayerAdmin)

class HandicapAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'handicap', 'effective_at', 'update_golf_round')
    ordering = ["-golfer"]
    readonly_fields=('handicap',)
admin.site.register(Handicap,HandicapAdmin)

def save_model(self, request, obj, form, change):
        # Step 1: Custom logic before saving
        if change:  # Check if it's an update
            obj.name = obj.name.upper()  # Example: Ensure the name is uppercase

        # Step 2: Call the original save method
        super().save_model(request, obj, form, change)

        # Step 3: Custom logic after saving
        if obj.stock < 10:
            self.message_user(request, f"Warning: Low stock for {obj.name}!", level='warning')