# from django.contrib import admin

from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static



app_name = 'mainapp'

urlpatterns = [
    path('', views.base, name='base'),
    path('home/', views.home, name="home"),
    path('about/', views.about, name='about'),
    path('table/', views.table, name='table'),
    path('team/', views.EditTeam, name='team'),
    path('matches/', views.matches, name='matches'),
    path('register/', views.register_form, name='register'),
    path('new_team/', views.new_team, name='newTeam'),
    path('new_teamTrainer/', views.new_teamTrainer, name='newTeamTrainer'),
    path('create_player/', views.create_player, name='create_player'),
    path('edit_player/<int:pesel>/', views.edit_player, name='edit_player'),
    path('delete_player/<int:pesel>/', views.delete_player, name='delete_player'),
    path('show_team_stats/<int:idTeam>/', views.show_team_stats, name='show_team_stats'),
    path('protocol_refree/<int:idMatch>/', views.protocol_refree, name='protocol_refree'),
    path('edit_stats_player/<int:pesel>/<int:idMatch>/', views.edit_match, name='edit_stats_player'),
    path('create_match/', views.create_match, name='create_match'),
    path('delete_match/<int:idMatch>/', views.delete_match, name='delete_match')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
