from django.conf.global_settings import MEDIA_URL
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from .models import *
from .Forms import UserForm, TeamForm, PlayerForm, PlayerEditForm, Protocol, MatchForm
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group


# Create your views here.


def base(request):
    return render(request, 'base.html')


def home(request):
    teams = Team.objects.all()
    return render(request, 'home.html', {'teams': teams})


def EditTeam(request):
    if request.user.groups.filter(name='Trener').exists():
        firstNameTrainer = request.user.first_name
        secondNameTrainer = request.user.last_name
        trainere = Trainer.objects.get_or_create(firstname=firstNameTrainer, secondname=secondNameTrainer)

        idTrainer = trainere[0].id_trainer

        try:
            idTeam = Team.objects.get(id_trainer=idTrainer).id_team
            number_of_players = Player.objects.filter(id_team=idTeam).count()

            logo = Team.objects.get(id_trainer=idTrainer).logo
            date_creation = Team.objects.get(id_trainer=idTrainer).date_creation

        except(KeyError, Team.DoesNotExist):
            return HttpResponseRedirect(reverse('mainapp:newTeamTrainer'))

        nameTeam = Team.objects.get(id_trainer=idTrainer).name
        players = Player.objects.filter(id_team=idTeam)
        return render(request, 'team.html',
                      {'players': players, 'nameTeam': nameTeam, 'logo': logo, 'date_creation': date_creation,
                       'number_of_players': number_of_players})
    else:
        return render(request, 'error.html', {'message': "Only trainers have permission to this section"})


def matches(request):
    queues = Queue.objects.all()
    try:
        selected_choice = Queue.objects.get(idQueue=request.GET['queueid'])
        matches = Match.objects.filter(idQueue=selected_choice)
    except(KeyError, Queue.DoesNotExist):
        return render(request, 'matches.html', {'queues': queues})
    else:
        return render(request, 'matches.html',
                      {'matches': matches, 'queues': queues, 'selected_choice': selected_choice})


def table(request):
    teamstats = StatsTeam.objects.all().order_by('-numberOfScores', '-numberOfMatchesWon')

    king_of_goals = StatsPlayerLeague.objects.all().order_by('-numberOfGoals')
    return render(request, 'teamstats.html', {'teamstats': teamstats, 'king_of_goals': king_of_goals})


def about(request):
    try:
        model = HTMLModels.objects.get(page_name='about')
    except ObjectDoesNotExist:
        return render(request, 'about.html')

    return render(request, 'about.html', {'model': model})


def register_form(request):
    form = UserForm(request.POST)

    if form.is_valid():
        user = form.save()
        group = form.cleaned_data['group_name']
        first_name = form.cleaned_data['first_name']
        second_name = form.cleaned_data['last_name']
        group.user_set.add(user)

        if str(group) == "Trener":
            trener = Trainer.objects.create(firstname=first_name, secondname=second_name)
            trener.save()
        return HttpResponseRedirect(reverse('mainapp:home'))
    else:
        form = UserForm()

    return render(request, 'register_form.html', {'form': form})


@login_required
def new_team(request):
    form = TeamForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('mainapp:home'))
    return render(request, 'team_form.html', {'form': form})


@login_required
def new_teamTrainer(request):
    form = TeamForm(request.POST or None, request.FILES or None)
    firstName = request.user.first_name
    lastName = request.user.last_name
    id_trainer = Trainer.objects.get(firstname=firstName, secondname=lastName).id_trainer
    if form.is_valid():
        form.save()
        name_team = form.cleaned_data['name']
        date_creation = form.cleaned_data['date_creation']
        # Team.objects.get(name=name_team,date_creation=date_creation)
        Team.objects.filter(name=name_team, date_creation=date_creation).update(id_trainer=id_trainer)
        return HttpResponseRedirect(reverse('mainapp:home'))
    return render(request, 'team_form.html', {'form': form})


@login_required
def create_player(request):
    if request.user.groups.filter(name='Trener').exists():

        form = PlayerForm(request.POST)
        firstName = request.user.first_name
        lastName = request.user.last_name
        id_trainer = Trainer.objects.get(firstname=firstName, secondname=lastName).id_trainer
        id_team = Team.objects.get(id_trainer=id_trainer).id_team

        # if Player.objects.filter(id_team=id_team).count() > 3:
        #     return render(request, 'error.html', {'message': "You can only create 2 players"})

        if form.is_valid():
            form.save()
            psl = form.cleaned_data['pesel']
            Player.objects.filter(pesel=psl).update(id_team=id_team)
            return HttpResponseRedirect(reverse('mainapp:team'))

        return render(request, 'RegisterTeamPlayer.html', {'form': form})
    else:
        return render(request, 'error.html', {'message': "Only trainers have permission to this section"})


@login_required
def edit_player(request, pesel):
    player = get_object_or_404(Player, pk=pesel)

    form = PlayerEditForm(request.POST or None, request.FILES or None, instance=player)

    if form.is_valid():
        status = form.cleaned_data['statusHealth']
        position = form.cleaned_data['position']
        age = form.cleaned_data['age']

        Player.objects.filter(pesel=pesel).update(statusHealth=status)
        Player.objects.filter(pesel=pesel).update(age=age)
        Player.objects.filter(pesel=pesel).update(position=position)
        return HttpResponseRedirect(reverse('mainapp:team'))

    return render(request, 'EditPlayer.html', {'form': form})


@login_required
def delete_player(request, pesel):
    player = get_object_or_404(Player, pk=pesel)

    if request.method == "POST":
        player.delete()
        return HttpResponseRedirect(reverse('mainapp:team'))

    return render(request, 'accept_delete_player.html', {'player': player})


def show_team_stats(request, idTeam):
    stats_team = get_object_or_404(StatsTeam, pk=idTeam)
    team = get_object_or_404(Team, pk=idTeam)
    count_scored_goals = 0
    for player in Player.objects.filter(id_team=idTeam):
        x = StatsPlayerLeague.objects.get(pesel=player.pesel).numberOfGoals
        count_scored_goals = count_scored_goals + x

    try:
        id_trainer = Trainer.objects.get(team__id_team=idTeam).id_trainer
        trainer = Trainer.objects.get(id_trainer=id_trainer)

    except ObjectDoesNotExist:
        return render(request, 'error.html', {'message': "Error"})
    return render(request, 'StatsTeam.html', {'stats_team': stats_team, 'team': team, 'trainer': trainer, 'count_scored_goals': count_scored_goals})


@login_required
def protocol_refree(request, idMatch):
    if request.user.groups.filter(name='Sedzia').exists():
        try:
            match = get_object_or_404(Match, pk=idMatch)
            home = match.Home
            guest = match.Guest
            id_home_team = Team.objects.get(id_team=home.id_team)
            id_guest_team = Team.objects.get(id_team=guest.id_team)

            for player in Player.objects.filter(id_team=id_home_team):
                try:
                    StatsPlayerMatch.objects.get(player=player, idMatch=match)
                except ObjectDoesNotExist:
                    StatsPlayerMatch.objects.create(player=player, idMatch=match)

            for player in Player.objects.filter(id_team=id_guest_team):
                try:
                    StatsPlayerMatch.objects.get(player=player, idMatch=match)
                except ObjectDoesNotExist:
                    StatsPlayerMatch.objects.create(player=player, idMatch=match)

            players_home = Player.objects.filter(id_team=id_home_team)
            players_guest = Player.objects.filter(id_team=id_guest_team)

        except ObjectDoesNotExist:
            return render(request, 'error.html', {'message': "That match doesnt exist"})

        return render(request, 'protocol_refree.html', {'match': match, 'players_home': players_home,
                                                        'players_guest': players_guest, 'homeTeam': id_home_team,
                                                        'guestTeam': id_guest_team})

    return render(request, 'error.html', {'message': "Only referees have permission to this section"})


@login_required
def edit_match(request, pesel, idMatch):
    global form, homeGoals, guestGoals

    if request.user.groups.filter(name='Sedzia').exists():

        id_player = get_object_or_404(Player, pk=pesel)
        stats = get_object_or_404(StatsPlayerMatch, player=id_player, idMatch=idMatch)
        home_team = Match.objects.get(idMatch=idMatch).Home
        guest_team = Match.objects.get(idMatch=idMatch).Guest
        match = get_object_or_404(Match, pk=idMatch)
        count_home_goals = 0
        count_guest_goals = 0
        current_goals = 0

        form = Protocol(request.POST or None, instance=stats)

        if form.is_valid():
            goals = form.cleaned_data['numberOfGoals']
            yellow_card = form.cleaned_data['numberOfYellowCard']
            StatsPlayerMatch.objects.filter(idMatch=idMatch, player=id_player).update(numberOfGoals=goals)
            StatsPlayerMatch.objects.filter(idMatch=idMatch, player=id_player).update(numberOfYellowCard=yellow_card)

            for match1 in Match.objects.all():
                if match1.Home == id_player.id_team or match1.Guest == id_player.id_team:
                    goals_in_match = StatsPlayerMatch.objects.get_or_create(idMatch=match1, player=id_player)[0].numberOfGoals
                    current_goals = current_goals + goals_in_match

            StatsPlayerLeague.objects.filter(pesel=id_player.pesel).update(numberOfGoals=current_goals)

            for player in Player.objects.filter(id_team=home_team):
                try:
                    x = StatsPlayerMatch.objects.get(player=player, idMatch=idMatch).numberOfGoals
                    count_home_goals = count_home_goals + x
                except ObjectDoesNotExist:
                    count_home_goals = count_home_goals + 0

            for player in Player.objects.filter(id_team=guest_team):
                try:
                    x = StatsPlayerMatch.objects.get(player=player, idMatch=idMatch).numberOfGoals
                    count_guest_goals = count_guest_goals + x
                except ObjectDoesNotExist:
                    count_guest_goals = count_guest_goals + 0

            #Match.objects.filter(idMatch=idMatch).update(homeGoals=count_home_goals)
            #Match.objects.filter(idMatch=idMatch).update(guestGoals=count_guest_goals)
            # match.homeGoals = count_home_goals
            # match.guestGoals = count_guest_goals
            # match.save()
            # if Match.finished_by_refree == -1:
            #     Match.save(match)

            match.save_stats(match, count_home_goals, count_guest_goals)


            return HttpResponseRedirect(reverse('mainapp:protocol_refree', args=(idMatch,)))

        return render(request, 'Edit_stats_player.html', {'form': form, 'idmatch': idMatch})
    else:
        return render(request, 'error.html', {'message': "Only referees have permission to this section"})



@login_required
def create_match(request):
    if request.user.groups.filter(name='Sedzia').exists():

            form = MatchForm(request.POST)

            if form.is_valid():
                form.save()
                Queue = form.cleaned_data['idQueue']
                home = form.cleaned_data['Home']
                guest = form.cleaned_data['Guest']
                Match.objects.filter(Home=home, Guest=guest, idQueue=Queue)
                return HttpResponseRedirect(reverse('mainapp:matches'))

            return render(request, 'createMatch.html', {'form': form})
    else:
        return render(request, 'error.html', {'message': "Only referees have permission to this section"})

@login_required
def delete_match(request, idMatch):
    if request.user.groups.filter(name='Sedzia').exists():

        match = get_object_or_404(Match, pk=idMatch)

        if request.method == "POST":
            return HttpResponseRedirect(reverse('mainapp:matches'))

        return render(request, 'accept_delete_match.html', {'match': match})
    else:
        return render(request, 'error.html', {'message': "Only referees have permission to this section"})
