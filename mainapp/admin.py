from .models import *
from rangefilter.filter import DateTimeRangeFilter, DateRangeFilter
from django.contrib import admin

from django_summernote.admin import SummernoteModelAdmin


# creating admin class
class blogadmin(SummernoteModelAdmin):
    # displaying posts with title slug and created time
    list_display = ('page_name',)
    # prepopulating slug from title
    summernote_fields = ('content',)


# registering admin class

admin.site.register(HTMLModels, blogadmin)
admin.site.register(StatsTeam)


@admin.register(StatsPlayerLeague)
class StatsPlayerLeagueAdmin(admin.ModelAdmin):
    list_display = ['get_player']

    def get_player(self, obj):
        return obj.pesel.firstName + " " + obj.pesel.secondName

    get_player.short_description = 'Imie i nazwisko'


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    search_fields = ['secondname']
    list_display = ['firstname', 'secondname']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'date_creation']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    search_fields = ['firstName', 'secondName', 'id_team__name']
    list_display = ['firstName', 'secondName', 'age', 'position', 'get_team', 'statusHealth']
    list_filter = ['position', 'id_team__name', 'age', 'statusHealth']

    def get_team(self, obj):
        if obj.id_team is not None:
            return obj.id_team.name

    get_team.short_description = 'Team'


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['idMatch', 'get_queue_name', 'startDate', 'get_home_team', 'get_guest_team']
    search_fields = ['idQueue__idQueue', 'Home__name', 'Guest__name']
    list_filter = [('Home__name', custom_titled_filter('Home Team')),
                   ('Guest__name', custom_titled_filter('Guest Team')),
                   ('idQueue__idQueue', custom_titled_filter('Number of Queue')),
                   ('startDate', DateTimeRangeFilter)]

    def get_queue_name(self, obj):
        return obj.idQueue.__str__()

    def get_home_team(self, obj):
        return obj.Home.name

    def get_guest_team(self, obj):
        return obj.Guest.name

    get_queue_name.short_description = 'Queue'
    get_home_team.short_description = 'Home Team'
    get_guest_team.short_description = 'Guest Team'


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ['get_name_queue', 'startDate', 'endDate']
    search_fields = ['idQueue']
    list_filter = [('idQueue', custom_titled_filter('Number of Queue')), ('startDate', DateRangeFilter),
    ('endDate', DateRangeFilter)]

    def get_name_queue(self, obj):
        return obj.__str__()

    get_name_queue.short_description = 'Queue'


@admin.register(StatsPlayerMatch)
class StatsPlayerMatchAdmin(admin.ModelAdmin):
    list_display = ['get_first_name', 'get_second_name', 'get_match',
                    'numberOfGoals', 'numberOfYellowCard']
    search_fields = ['player__firstName', 'player__secondName']
    list_filter = [('numberOfYellowCard', custom_titled_filter('YellowCard')),
                   ('numberOfGoals', custom_titled_filter('Goals'))]

    def get_first_name(self, obj):
        return obj.player.firstName

    def get_second_name(self, obj):
        return obj.player.secondName

    def get_match(self, obj):
        return str(obj.idMatch.__str__())

    get_first_name.short_description = 'First Name'
    get_second_name.short_description = 'Second Name'
    get_match.short_description = 'Match'
