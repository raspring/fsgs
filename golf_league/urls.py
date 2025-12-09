from django.urls import path, reverse_lazy
from . import views
#homepage will be naviation and season pts race - must be logged in
app_name='golf_league'
urlpatterns = [
    path("events/", views.Events_ListView.as_view(), name='events_list'),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name='event_detail'),
    path("events/<int:pk>/addplayer", views.EventPlayerCreateView.as_view(), name='event_player_create'),
    path("eventplayer/delete/<int:pk>",views.EventPlayerDeleteView.as_view(), name='event_player_delete'),
    path("eventplayer/update/<int:pk>",views.EventPlayerUpdateView.as_view(), name='event_player_update'),
    path("eventplayer/update_score/<int:pk>",views.PlayedRoundUpdate.as_view(), name='played_round_create'),
    path("events/<int:pk>/extract", views.export_users_csv, name='event_player_extract'),
    path("events/upload/<int:pk>/", views.UploadView.as_view(), name='results_upload'),
    path("handicaps/", views.Handicap_ListView.as_view(), name = 'handicaps_summary'),
    path("handicaps/detail/<int:pk>/", views.Handicap_DetailView.as_view(), name = 'handicaps_detail'),
    path("season_points/", views.SeasonPoints_ListView.as_view(), name = 'season_points'),
    path("season_points_test/", views.SeasonPoints_ListView_test.as_view(), name = 'season_points_test'),
    path("events/backup/extract", views.export_playedrounds_csv, name='playedrounds_extract'),
]