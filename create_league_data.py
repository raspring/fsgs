# create_tasks.py
 
def main():

    PlayedRound.objects.all().delete()
    EventPlayer.objects.all().delete()
    Handicap.objects.all().delete()
    LeagueEvent.objects.all().delete()
    LeaguePlayer.objects.all().delete()
    LeagueSeason.objects.all().delete()
    
    data_league_seasons = pd.read_excel('league_data.xlsx', sheet_name="league_seasons")
    data_league_events = pd.read_excel('league_data.xlsx', sheet_name="league_events")
    data_league_players = pd.read_excel('league_data.xlsx', sheet_name="league_players")
    data_initial_hdcps = pd.read_excel('league_data.xlsx', sheet_name="initial_handicaps")
    data_played_round = pd.read_excel('league_data.xlsx', sheet_name="Played_Round")

    #data_players_recent = pd.read_excel('league_data.xlsx', sheet_name="recent")

    #create season objects
    for index, row in data_league_seasons.iterrows():
        season_name = row.iloc[0]
        LeagueSeason.objects.get_or_create(name=season_name)

    #create event objects
    for index, row in data_league_events.iterrows():
        season, created = LeagueSeason.objects.get_or_create(name=row.iloc[1])
        date = row.iloc[2]
        golf_course = row.iloc[3]
        event_status = row.iloc[4]
        LeagueEvent.objects.get_or_create(leagueseason=season, event_date=date,event_golf_course=golf_course, event_status = event_status) 
    
    #create leagueplayer objects
    for index, row in data_league_players.iterrows():
        first_name = row.iloc[2]
        last_name = row.iloc[3]
        gender = row.iloc[4]
        LeaguePlayer.objects.get_or_create(first_name=first_name, last_name=last_name, gender=gender)

    #create initial handicap objects
    for index, row in data_initial_hdcps.iterrows():
        first_name = row.iloc[3]
        last_name = row.iloc[4]
        leagueplayerobject = LeaguePlayer.objects.get(first_name=first_name, last_name=last_name)
        effective_date = row.iloc[2]
        handicap = row.iloc[5]
        update_user = row.iloc[7]
        update_comment = row.iloc[8]
        Handicap.objects.create(golfer=leagueplayerobject, handicap=handicap, effective_at=effective_date,update_user=update_user,update_comment=update_comment)

    #create played round objects
    for index, row in data_played_round.iterrows():
        event_date = row.iloc[10]
        new_player_flag = row.iloc[8]
        first_name = row.iloc[11]
        last_name = row.iloc[12]
        round_old_hdcp = row.iloc[1]
        round_old_hdcp_eff = row.iloc[13]
        round_new_hdcp = row.iloc[6]
        round_new_hdcp_eff = row.iloc[14]
        gross_score = row.iloc[4]
        net_score = row.iloc[3]
        handicap_adjustment = row.iloc[5]
        net_rel_par = row.iloc[2]
        coconut = row.iloc[7]

        league_event = LeagueEvent.objects.get(event_date=event_date)
        leagueplayerobject = LeaguePlayer.objects.get(first_name=first_name, last_name=last_name)
        '''conditional here to crate new handicpa object - should only be if '''
        if Handicap.objects.filter(golfer=leagueplayerobject).exists():
            latest_handicap = Handicap.objects.filter(golfer=leagueplayerobject).latest("effective_at")
            if round_old_hdcp == latest_handicap.handicap:
                round_handicap = latest_handicap
            else:
                round_handicap = Handicap.objects.create(golfer=leagueplayerobject, handicap=round_old_hdcp, effective_at=round_old_hdcp_eff,update_user="rob springett",update_comment="manual handicap update")
        else:
            round_handicap = Handicap.objects.create(golfer=leagueplayerobject, handicap=round_old_hdcp, effective_at=round_old_hdcp_eff,update_user="rob springett",update_comment="manual handicap update")
        comment = "Update from FSGS game"
        event_player = EventPlayer.objects.create(golfer=leagueplayerobject,league_event=league_event,new_player_flag=new_player_flag,round_handicap=round_handicap)
        round = PlayedRound.objects.create(event_player=event_player, gross_score=gross_score, net_score=net_score, net_rel_par=net_rel_par,coconut_pts=coconut,handicap_adjustment=handicap_adjustment)
        Handicap.objects.create(golfer=leagueplayerobject, handicap=round_new_hdcp, effective_at=round_new_hdcp_eff,update_golf_round=round,update_comment=comment)

    '''for index, row in data_players_recent.iterrows():
        event_date = row.iloc[9]
        league_event = LeagueEvent.objects.get(event_date=event_date)
        new_player_flag = row.iloc[8]
        first_name = row.iloc[10]
        last_name = row.iloc[11]
        leagueplayer = LeaguePlayer.objects.get(first_name=first_name, last_name=last_name)
        if new_player_flag == "N":
            handicap = Handicap.objects.filter(golfer=leagueplayer)
            if handicap.exists():
                handicap = handicap.latest('effective_at')
        else:
            comment = "Initial handicap"
            round_new_hdcp = row.iloc[1]
            handicap = Handicap.objects.create(golfer=leagueplayer, handicap=round_new_hdcp, effective_at=event_date,update_comment=comment)

        event_player = EventPlayer.objects.create(golfer=leagueplayer,league_event=league_event,new_player_flag=new_player_flag,round_handicap=handicap)
 '''
if __name__ == "__main__":
    import os
 
    from django.core.wsgi import get_wsgi_application
    import pandas as pd
 
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FSGS.settings")
    application = get_wsgi_application()
    
    from golf_league.models import LeaguePlayer, Handicap, LeagueSeason, LeagueEvent, PlayedRound, EventPlayer
    
    main()