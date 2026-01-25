#from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import OuterRef, Subquery, Sum, Count
import datetime
import pandas as pd
import csv
from io import TextIOWrapper
from django.http import HttpResponse
from django.db.models import F, Window
from django.db.models.functions import Rank
import decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import LeagueEvent, Handicap, EventPlayer, PlayedRound, LeaguePlayer, LeagueSeason
from .forms import UpdateEventPlayerForm, CreateLeaguePlayerForm, CreateEventPlayerForm, UploadScoresForm, CreatePlayedRoundForm

class Events_ListView(ListView):
    model = LeagueEvent
    #template_name = "myarts/article_list.html"
    ordering = ['-event_date']

class Handicap_ListView(ListView):
    model = Handicap

    def get(self, request):
        max_ids = Handicap.objects.filter(golfer=OuterRef('golfer')).order_by('-effective_at').values('id')
        x = Handicap.objects.filter(id=Subquery(max_ids[:1])).order_by('golfer__first_name')
        context = { 'handicap_list' : x}
        return render(request, 'golf_league/handicap_list.html', context)
    
class Handicap_DetailView(ListView):
    model = Handicap
    def get(self, request, pk):
        league_player = get_object_or_404(LeaguePlayer, id=pk)
        x = Handicap.objects.filter(golfer=league_player).order_by('-effective_at')
        context = { 'handicap_list' : x}
        return render(request, 'golf_league/handicap_detail.html', context)

class EventDetailView(DetailView):
    model = LeagueEvent

    def get(self, request, pk) :
        x = get_object_or_404(LeagueEvent, id=pk)
        playedrounds = PlayedRound.objects.filter(event_player__league_event=x).order_by('event_player__new_player_flag','net_rel_par').annotate(rank=Window(expression=Rank(),order_by=F('coconut_pts').desc()))
        event_player = EventPlayer.objects.filter(league_event=x)
        context = { 'leagueevent' : x, 'eventplayer':event_player,'playedround': playedrounds}
        return render(request,'golf_league/leagueevent_detail.html', context)
    
class EventPlayerDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/admin/login/'
    model = EventPlayer

    def get_success_url(self):
        event = self.object.league_event
        return reverse('golf_league:event_detail', args=[event.id])


class EventPlayerUpdateView(LoginRequiredMixin, View):
    login_url = '/admin/login/'
    #need a form
    template_name = 'golf_league/eventplayer_update.html'

    def get(self, request, pk):
        eventplayer = get_object_or_404(EventPlayer, id=pk)
        player_name = eventplayer.golfer
        form = UpdateEventPlayerForm(instance=eventplayer)
        ctx = {'form': form, 'eventplayer':player_name}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        eventplayer = get_object_or_404(EventPlayer, id=pk)
        success_url = reverse('golf_league:event_detail', args=[eventplayer.league_event.id])
        form = UpdateEventPlayerForm(request.POST, instance=eventplayer)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        new_handicap = round(form.cleaned_data['handicap'] * 2)/2
        update_comment = form.cleaned_data['update_comment']
        golfer = eventplayer.golfer
        effective_dt = datetime.date.today()
        handicap = Handicap.objects.create(golfer=golfer, handicap=new_handicap, effective_at=effective_dt,update_comment=update_comment)

        eventplayer.round_handicap = handicap
        eventplayer.save()

        return redirect(success_url)


class EventPlayerCreateView(LoginRequiredMixin, View):
    login_url = '/admin/login/'
    template_name = 'golf_league/eventplayer_create.html'

    def get(self, request, pk=None):
        #pk is of the event
        event_player_form = CreateEventPlayerForm()
        league_player_form = CreateLeaguePlayerForm()
        ctx = {'event_player_form': event_player_form,'league_player_form':league_player_form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        #pk is of the event
        success_url = reverse('golf_league:event_detail', args=[pk])
        league_event = LeagueEvent.objects.get(id=pk)
        if 'event_player' in request.POST:
            form = CreateEventPlayerForm(request.POST)
            if not form.is_valid():
                league_player_form = CreateLeaguePlayerForm()
                ctx = {'event_player_form': form,'league_player_form':league_player_form}
                return render(request, self.template_name, ctx)
        if 'league_player' in request.POST:
            form = CreateLeaguePlayerForm(request.POST)
            if not form.is_valid():
                event_player_form = CreateEventPlayerForm()
                ctx = {'event_player_form': event_player_form,'league_player_form':form}
                return render(request, self.template_name, ctx)
        
        if 'event_player' in request.POST:
            leagueplayer = form.cleaned_data['league_player_id']

            if EventPlayer.objects.filter(league_event=league_event, golfer=leagueplayer).exists():
                ctx = {'event_player_form': form,'message':leagueplayer.first_name + " is already registered for event"}
                return render(request, self.template_name, ctx)
        
            else:
                handicap = Handicap.objects.filter(golfer=leagueplayer)
                if handicap.exists():
                    new_player_flag = "N"
                    handicap = handicap.latest('created_at')
                    eventplayer, created = EventPlayer.objects.get_or_create(golfer=leagueplayer,league_event=league_event,new_player_flag=new_player_flag,round_handicap=handicap)
                else:
                    new_player_flag = "Y"
                    eventplayer, created = EventPlayer.objects.get_or_create(golfer=leagueplayer,league_event=league_event,new_player_flag=new_player_flag)
                return redirect(success_url)
        
        if 'league_player' in request.POST:
            first_name = form.cleaned_data['first_name'].title()
            last_name = form.cleaned_data['last_name'].title()
            gender = form.cleaned_data['gender']
            leagueplayer = LeaguePlayer.objects.create(first_name=first_name, last_name=last_name,gender=gender)
            if form.cleaned_data['handicap'] is not None:
                handicap = round(form.cleaned_data['handicap'] * 2)/2
                update_comment = 'Initial Handicap'
                if gender == "M" and handicap > 25:
                    handicap = 25
                    update_comment = update_comment + "- max hdcp applied"
                elif gender == "F" and handicap > 28:
                    handicap = 28
                    update_comment = update_comment + "- max hdcp applied"

                effective_dt = datetime.date.today()
                handicap = Handicap.objects.create(golfer=leagueplayer, handicap=handicap, effective_at=effective_dt,update_comment=update_comment)
                EventPlayer.objects.get_or_create(golfer=leagueplayer,league_event=league_event,new_player_flag="Y",round_handicap=handicap)
            else:
                EventPlayer.objects.get_or_create(golfer=leagueplayer,league_event=league_event,new_player_flag="Y")
            
            return redirect(success_url)
        
class SeasonPoints_ListView(View):
    template_name = 'golf_league/season_points.html'
    def get(self, request):
        seasons = LeagueSeason.objects.all().order_by('-name')
        selected_season = request.GET.get('season')

        if selected_season:
            season_filter = selected_season
        elif seasons.exists():
            season_filter = seasons.first().name
        else:
            season_filter = None

        if season_filter:
            playedrounds = PlayedRound.objects.filter(
                event_player__league_event__leagueseason__name=season_filter
            ).values(
                'event_player__golfer',
                'event_player__golfer__first_name',
                'event_player__golfer__last_name'
            ).annotate(
                coconut_pts=Sum('coconut_pts')
            ).annotate(
                event_count=Count('event_player__league_event')
            ).order_by('-coconut_pts')
        else:
            playedrounds = []

        temp_list = [x['coconut_pts'] for x in playedrounds]
        for record in playedrounds:
            record["rank"] = temp_list.index(record['coconut_pts']) + 1

        ctx = {'rounds': playedrounds, 'seasons': seasons, 'selected_season': season_filter}
        return render(request, self.template_name, ctx)

@login_required 
def export_users_csv(request, pk):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="FSGS_extract.csv"'

    writer = csv.writer(response,dialect='excel')
    x = get_object_or_404(LeagueEvent, id=pk)
    event_player = EventPlayer.objects.filter(league_event=x).values_list('golfer__first_name','golfer__last_name','golfer__gender','round_handicap__handicap')
    df = pd.DataFrame(list(event_player))
    df.columns = ['First', 'Last', 'Gender', 'Handicap']
    df['Email'] = ""
    df['WHS ID'] = ""
    df['Team'] = ""
    df['Tee'] = ""
    df['Registered'] = ""
    df['Transport'] = ""
    df['Phone'] = ""
    df = df[['First', 'Last', 'Email', 'Phone', 'Gender', 'WHS ID', 'Handicap', 'Team', 'Tee', 'Registered', 'Transport']]
    writer.writerow([column for column in df.columns])
    writer.writerows(df.values.tolist())
    return response

class UploadView(View):
    template_name = 'golf_league/upload_result.html'

    def get(self, request,pk=None):
        row_count = 0
        ctx = {"form": UploadScoresForm(),"row_count": row_count,'pk':pk}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        leagueevent = get_object_or_404(LeagueEvent, id=pk)
        #success_url = reverse('golf_league:event_detail', args=[pk])
        results_file = request.FILES["results_file"]
        rows = TextIOWrapper(results_file, encoding="utf-8", newline="")
        for row in csv.reader(rows):
            if "Tee" in row[1]:
                name = row[0].split()
                if len(name)==2:
                    first_name = name[0]
                    last_name = name[1]
                else:
                    first_name = name[0]
                    last_name = name[1] + name[2]
                try:
                    eventplayer = EventPlayer.objects.get(league_event=leagueevent,golfer__first_name=first_name,golfer__last_name=last_name)
                    gross = row[23]
                    net = gross - round(float(eventplayer.round_handicap.handicap),0)
                    net_rel_par = net - 72
                    gender = eventplayer.golfer.gender
                    if net_rel_par == 0:
                        hdcp_adj = 0
                    elif net_rel_par < 0:
                        hdcp_adj = net_rel_par*0.5
                    else:
                        if gender == "M" and eventplayer.round_handicap.handicap + 1 <= 25:
                            hdcp_adj = 1.0
                        elif gender == "M" and eventplayer.round_handicap.handicap + 0.5 <= 25:
                            hdcp_adj = 0.5
                        elif gender == "F" and eventplayer.round_handicap.handicap + 1 <= 28:
                            hdcp_adj = 1.0
                        elif gender == "F" and eventplayer.round_handicap.handicap + 0.5 <= 28:
                            hdcp_adj = 0.5
                        else:
                            hdcp_adj = 0.0
                    new_handicap = decimal.Decimal(hdcp_adj) + decimal.Decimal(eventplayer.round_handicap.handicap)
                    if eventplayer.new_player_flag == "Y":
                        played_round = PlayedRound.objects.create(event_player=eventplayer,league_event=leagueevent,gross_score=gross,net_score=net,net_rel_par=net_rel_par,handicap_adjustment=hdcp_adj,coconut_pts=5)
                        eventplayer.played_round = played_round
                        eventplayer.save()
                    else:
                        played_round = PlayedRound.objects.create(event_player=eventplayer,league_event=leagueevent,gross_score=gross,net_score=net,net_rel_par=net_rel_par,handicap_adjustment=hdcp_adj)
                        eventplayer.played_round = played_round
                        eventplayer.save()
                    playedrounds = PlayedRound.objects.filter(event_player__league_event=leagueevent, event_player__new_player_flag="N")
                    scores_list = [x.net_score for x in playedrounds]
                    scores_list.sort()
                    for golfround in playedrounds:
                        net = golfround.net_score
                        rank = scores_list.index(net)
                        if rank > 9 :
                            pts = 5
                        else:
                            number = len(playedrounds.filter(net_score=net))
                            pts = round(sum(coconut[rank:rank+number])/number,0)
                        golfround.coconut_pts=pts
                        golfround.save()
                    Handicap.objects.create(golfer=eventplayer.golfer, handicap=new_handicap, effective_at=leagueevent.event_date,update_golf_round=played_round,update_comment="Update from FSGS event")
                except:
                    print('no object')
        return render(request, "golf_league/upload_result.html", {"form": UploadScoresForm(),'row':perm_row,'name':first_name})


class PlayedRoundUpdate(LoginRequiredMixin, View):
    login_url = '/admin/login/'
    #need a form
    template_name = 'golf_league/eventplayer_update_score.html'

    def get(self, request, pk):
        eventplayer = get_object_or_404(EventPlayer, id=pk)
        form = CreatePlayedRoundForm(instance=eventplayer)
        ctx = {'form': form,'player':eventplayer}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        coconut = [100,90,80,70,60,50,40,30,20,10]
        eventplayer = get_object_or_404(EventPlayer, id=pk)
        league_event = get_object_or_404(LeagueEvent,id=eventplayer.league_event.id)
        success_url = reverse('golf_league:event_detail', args=[eventplayer.league_event.id])
        form = CreatePlayedRoundForm(request.POST, instance=eventplayer)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        gross = form.cleaned_data['gross_score']
        net = gross - round(float(eventplayer.round_handicap.handicap),0)
        net_rel_par = net - 72
        gender = eventplayer.golfer.gender
        #add logic to calculate hdcp adj
        if net_rel_par == 0:
            hdcp_adj = 0
        elif net_rel_par < 0:
            hdcp_adj = net_rel_par*0.5
        else:
            if gender == "M" and eventplayer.round_handicap.handicap + 1 <= 25:
                hdcp_adj = 1.0
            elif gender == "M" and eventplayer.round_handicap.handicap + decimal.Decimal(0.5) <= 25:
                hdcp_adj = 0.5
            elif gender == "F" and eventplayer.round_handicap.handicap + 1 <= 28:
                hdcp_adj = 1.0
            elif gender == "F" and eventplayer.round_handicap.handicap + decimal.Decimal(0.5) <= 28:
                hdcp_adj = 0.5
            else:
                hdcp_adj = 0.0
            
        new_handicap = decimal.Decimal(hdcp_adj) + decimal.Decimal(eventplayer.round_handicap.handicap)
        if eventplayer.new_player_flag == "Y":
            played_round = PlayedRound.objects.create(event_player=eventplayer,gross_score=gross,net_score=net,net_rel_par=net_rel_par,coconut_pts=5,handicap_adjustment=hdcp_adj)
            eventplayer.played_round = played_round
            eventplayer.save()


        else:
            played_round = PlayedRound.objects.create(event_player=eventplayer,gross_score=gross,net_score=net,net_rel_par=net_rel_par,handicap_adjustment=hdcp_adj)
            eventplayer.played_round = played_round
            eventplayer.save()
            playedrounds = PlayedRound.objects.filter(event_player__league_event=league_event, event_player__new_player_flag="N")
            for golfround in playedrounds:
                scores_list = [x.net_score for x in playedrounds]
                scores_list.sort()
                net = golfround.net_score
                rank = scores_list.index(net)
                if rank > 9 :
                    pts = 5
                else:
                    number = len(playedrounds.filter(net_score=net))
                    pts = round(sum(coconut[rank:rank+number])/number,0)
                golfround.coconut_pts=pts
                golfround.save()
        Handicap.objects.create(golfer=eventplayer.golfer, handicap=new_handicap, effective_at=league_event.event_date,update_golf_round=played_round,update_comment="Update from FSGS event")
        return redirect(success_url)
    
class SeasonPoints_ListView_test(View):
    template_name = 'golf_league/season_points_test.html'
    def get(self, request):
        playedrounds = PlayedRound.objects.all().values('event_player__golfer','event_player__golfer__first_name','event_player__golfer__last_name','event_player__league_event__leagueseason__name').  \
            annotate(coconut_pts=Sum('coconut_pts')).  \
                annotate(event_count=Count('event_player__league_event')).order_by('-coconut_pts').  \
                    annotate(rank=Window(expression=Rank(),partition_by=F('event_player__league_event__leagueseason__name'),order_by=F('coconut_pts').desc()))

        seasons = LeagueSeason.objects.all()

        ctx = {'rounds': playedrounds, 'seasons':seasons}
        return render(request, self.template_name, ctx)

@login_required
def export_playedrounds_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="FSGS_extract.csv"'
    writer = csv.writer(response,dialect='excel')
    df = pd.DataFrame(list(PlayedRound.objects.all().values()))

    rounds = pd.DataFrame(list(PlayedRound.objects.all().values()))
    eventplayers = pd.DataFrame(list(EventPlayer.objects.all().values()))
    league_players = pd.DataFrame(list(LeaguePlayer.objects.all().values()))
    league_events = pd.DataFrame(list(LeagueEvent.objects.all().values()))
    handicaps = pd.DataFrame(list(Handicap.objects.all().values()))

    df = rounds.merge(eventplayers,how='left',left_on='event_player_id',right_on='id')
    df = df.merge(league_players,how='left',left_on='golfer_id',right_on='id')
    del df['id']
    df = df.merge(league_events,how='left',left_on='league_event_id',right_on='id')
    del df['id']
    df = df.merge(handicaps,how='left',left_on='round_handicap_id',right_on='id')

    df = df[['first_name','last_name','gender','event_date','event_golf_course','handicap','update_comment','gross_score','net_score','net_rel_par','coconut_pts','handicap_adjustment','new_player_flag']]
  
    writer.writerow([column for column in df.columns])
    writer.writerows(df.values.tolist())
    return response