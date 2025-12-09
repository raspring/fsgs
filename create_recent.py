def main():
    data_players_recent = pd.read_excel('league_data.xlsx', sheet_name="may")

    for index, row in data_players_recent.iterrows():
        event_date = row.iloc[9]
        league_event = LeagueEvent.objects.get(event_date=event_date)
        new_player_flag = row.iloc[8]
        first_name = row.iloc[10]
        last_name = row.iloc[11]
        leagueplayer = LeaguePlayer.objects.get(first_name=first_name, last_name=last_name)
        if new_player_flag == "N":
            handicap = Handicap.objects.filter(golfer=leagueplayer)
            if handicap.exists():
                handicap = handicap.latest('created_at')
                event_player = EventPlayer.objects.create(golfer=leagueplayer,league_event=league_event,new_player_flag=new_player_flag,round_handicap=handicap)
            else:
                event_player = EventPlayer.objects.create(golfer=leagueplayer,league_event=league_event,new_player_flag=new_player_flag)
        else:
            comment = "Initial handicap"
            round_new_hdcp = row.iloc[1]
            handicap = Handicap.objects.create(golfer=leagueplayer, handicap=round_new_hdcp, effective_at=event_date,update_comment=comment)
            event_player = EventPlayer.objects.create(golfer=leagueplayer,league_event=league_event,new_player_flag=new_player_flag,round_handicap=handicap)
 
if __name__ == "__main__":
    import os
 
    from django.core.wsgi import get_wsgi_application
    import pandas as pd
 
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FSGS.settings")
    application = get_wsgi_application()
    
    from golf_league.models import LeaguePlayer, Handicap, LeagueSeason, LeagueEvent, PlayedRound, EventPlayer
    
    main()