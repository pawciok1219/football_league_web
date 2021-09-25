from django.core.exceptions import ValidationError
from django.core.validators import \
    MaxValueValidator, RegexValidator, MinValueValidator
from django.db import models
import datetime

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager
from django.shortcuts import get_object_or_404


class HTMLModels(models.Model):
    page_name = models.CharField(max_length=25)
    content = models.TextField(max_length=500)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, name, surname, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)


class Trainer(models.Model):
    firstname = models.CharField(max_length=50)
    secondname = models.CharField(max_length=50)
    id_trainer = models.AutoField(primary_key=True)

    def __str__(self):
        return str(self.firstname) + " " + str(self.secondname)

    def getId(self):
        return self.id_trainer


class Team(models.Model):
    id_team = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    date_creation = models.DateField(auto_now=False, validators=[MaxValueValidator(datetime.date.today())])
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    id_trainer = models.OneToOneField(Trainer, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = True if not self.id_team else False
        super().save(*args, **kwargs)
        if is_new:
            team = StatsTeam.objects.create(idTeam=self)
            team.save()


class Player(models.Model):
    POSITION = [
        ('N', 'Napastnik'),
        ('BR', 'Bramkarz'),
        ('LP', 'Lewy pomocnik'),
        ('PP', 'Prawy pomocnik'),
        ('LS', 'Lewy skrzydlowy'),
        ('PS', 'Prawy skrzydlowy'),
        ('SO', 'Srodkowy obronca'),
        ('LO', 'Lewy obronca'),
        ('PO', 'Prawy obronca')
    ]

    STATUS = [
        ('KO', 'Kontuzjowany'),
        ('ZD', 'Zdrowy'),
        ('RH', 'Rehabilitacja'),
    ]

    pesel = models.PositiveIntegerField(primary_key=True,
                                        validators=[MaxValueValidator(99999999999), MinValueValidator(70999999999)])
    firstName = models.CharField(max_length=25, validators=[RegexValidator('^[a-zA-Z]+$', message="Tylko litery")])
    secondName = models.CharField(max_length=25, validators=[RegexValidator('^[a-zA-Z]+$', message="Tylko litery")])
    position = models.CharField(max_length=25, choices=POSITION,
                                validators=[RegexValidator('^[a-zA-Z]+$', message="Tylko litery")])
    age = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100), MinValueValidator(10)])
    statusHealth = models.CharField(max_length=2, choices=STATUS, default='ZDROWY')
    id_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.firstName) + " " + str(self.secondName)

    def save(self, *args, **kwargs):
        is_new = True if not self.pesel else False
        super().save(*args, **kwargs)
        playerstats = StatsPlayerLeague.objects.create(pesel=self)
        playerstats.save()


class StatsPlayerLeague(models.Model):
    pesel = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True)
    numberOfMinutes = models.PositiveIntegerField(default=0)
    numberOfAssists = models.PositiveIntegerField(default=0)
    numberOfGoals = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.pesel.firstName) + " " + str(self.pesel.secondName)


class Queue(models.Model):
    idQueue = models.AutoField(primary_key=True)
    startDate = models.DateField(auto_now=False)
    endDate = models.DateField(auto_now=False)

    def __str__(self):
        return "Kolejka nr " + str(self.idQueue)


class StatsTeam(models.Model):
    idTeam = models.OneToOneField(Team, on_delete=models.CASCADE, primary_key=True)
    numberOfGoalsLost = models.PositiveIntegerField(default=0)
    numberOfGoalsScored = models.PositiveIntegerField(default=0)
    numberOfMatchesWon = models.PositiveIntegerField(default=0)
    numberOfDraws = models.PositiveIntegerField(default=0)
    numberOfMatchesLost = models.PositiveIntegerField(default=0)
    numberOfScores = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.idTeam)


class Match(models.Model):
    idMatch = models.AutoField(primary_key=True)
    idQueue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    Home = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="Home")
    Guest = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="Guest")
    homeGoals = models.PositiveSmallIntegerField(default=0)
    guestGoals = models.PositiveSmallIntegerField(default=0)
    startDate = models.DateTimeField(auto_now=False)
    finished_by_refree = models.IntegerField(default=-1)

    def __str__(self):
        return str(self.Home) + " - " + str(self.Guest)

    def save_stats(self, match, new_homeGoals, new_guestGoals):

        hometeam = StatsTeam.objects.get(idTeam=match.Home.id_team)
        guestteam = StatsTeam.objects.get(idTeam=match.Guest.id_team)

        if match.finished_by_refree == -1:

            if new_homeGoals == new_guestGoals:  # jesli remis
                hometeam.numberOfDraws = hometeam.numberOfDraws + 1
                guestteam.numberOfDraws = guestteam.numberOfDraws + 1
            elif new_homeGoals > new_guestGoals:  # jesli gospodarz wygral
                hometeam.numberOfMatchesWon = hometeam.numberOfMatchesWon + 1
                guestteam.numberOfMatchesLost = guestteam.numberOfMatchesLost + 1
            elif new_homeGoals < new_guestGoals:  # jesli gosc wygral
                hometeam.numberOfMatchesLost = hometeam.numberOfMatchesLost + 1
                guestteam.numberOfMatchesWon = guestteam.numberOfMatchesWon + 1

            match.finished_by_refree = 0
            match.homeGoals = new_homeGoals
            match.guestGoals = new_guestGoals
            match.save()

        else:
            if new_homeGoals == new_guestGoals:  # jesli remis
                if match.homeGoals == match.guestGoals:
                    True
                elif match.homeGoals > match.guestGoals:
                    hometeam.numberOfMatchesWon -= 1
                    guestteam.numberOfMatchesLost -= 1
                    hometeam.numberOfDraws += 1
                    guestteam.numberOfDraws += 1
                elif match.homeGoals < match.guestGoals:
                    hometeam.numberOfMatchesLost -= 1
                    guestteam.numberOfMatchesWon -= 1
                    hometeam.numberOfDraws += 1
                    guestteam.numberOfDraws += 1
            elif new_homeGoals > new_guestGoals:  # jesli gospodarz wygral
                if match.homeGoals == match.guestGoals:
                    hometeam.numberOfDraws -= 1
                    guestteam.numberOfDraws -= 1
                    hometeam.numberOfMatchesWon += 1
                    guestteam.numberOfMatchesLost += 1
                elif match.homeGoals > match.guestGoals:
                    True
                elif match.homeGoals < match.guestGoals:
                    hometeam.numberOfMatchesLost -= 1
                    guestteam.numberOfMatchesWon -= 1
                    hometeam.numberOfMatchesWon += 1
                    guestteam.numberOfMatchesLost += 1
            elif new_homeGoals < new_guestGoals:  # jesli gosc wygral
                if match.homeGoals == match.guestGoals:
                    hometeam.numberOfDraws -= 1
                    guestteam.numberOfDraws -= 1
                    hometeam.numberOfMatchesLost += 1
                    guestteam.numberOfMatchesWon += 1
                elif match.homeGoals > match.guestGoals:
                    hometeam.numberOfMatchesWon -= 1
                    guestteam.numberOfMatchesLost -= 1
                    hometeam.numberOfMatchesLost += 1
                    guestteam.numberOfMatchesWon += 1
                elif match.homeGoals < match.guestGoals:
                    True

        match.homeGoals = new_homeGoals
        match.guestGoals = new_guestGoals
        match.save()

        hometeam.numberOfScores = 3 * hometeam.numberOfMatchesWon + 1 * hometeam.numberOfDraws
        guestteam.numberOfScores = 3 * guestteam.numberOfMatchesWon + 1 * guestteam.numberOfDraws

        hometeam.save()
        guestteam.save()

    def delete(self, *args, **kwargs):
        hometeam = StatsTeam.objects.get(idTeam=self.Home.id_team)
        guestteam = StatsTeam.objects.get(idTeam=self.Guest.id_team)

        for player in Player.objects.all():
            if player.id_team == hometeam.idTeam or player.id_team == guestteam.idTeam:
                y = StatsPlayerMatch.objects.get(player=player, idMatch=self.idMatch).numberOfGoals
                x = StatsPlayerLeague.objects.get(pesel=player.pesel).numberOfGoals
                z = x - y
                StatsPlayerLeague.objects.filter(pesel=player.pesel).update(numberOfGoals=z)


        homeGoals = self.homeGoals
        guestGoals = self.guestGoals

        if homeGoals == guestGoals:  # jesli remis
            hometeam.numberOfDraws -= 1
            guestteam.numberOfDraws -= 1

            hometeam.numberOfScores -= 1
            guestteam.numberOfScores -= 1

        elif homeGoals > guestGoals:  # jesli gospodarz wygral
            hometeam.numberOfMatchesWon -= 1
            guestteam.numberOfMatchesLost -= 1

            hometeam.numberOfScores -= 3
        elif homeGoals < guestGoals:  # jesli gosc wygral
            hometeam.numberOfMatchesLost -= 1
            guestteam.numberOfMatchesWon -= 1

            guestteam.numberOfScores -= 3

        hometeam.save()
        guestteam.save()

        return super(Match, self).delete()



    def comparator(home, guest):
        if home == guest:
            raise ValidationError("Druzyny nie moga grac miedzy soba")








    # def save(self, *args, **kwargs):
    #     is_new = True if not self.idMatch else False
    #
    #     if not is_new:
    #         x = get_object_or_404(Match, pk=self.idMatch)
    #         homeGoals = x.homeGoals
    #         guestGoals = x.guestGoals
    #
    #     super().save(*args, **kwargs)
    #     hometeam = StatsTeam.objects.get(idTeam=self.Home)
    #     guestteam = StatsTeam.objects.get(idTeam=self.Guest)
    #
    #     if is_new:
    #
    #         if self.homeGoals == self.guestGoals:  # jesli remis
    #             hometeam.numberOfDraws += 1
    #             guestteam.numberOfDraws += 1
    #         elif self.homeGoals > self.guestGoals:  # jesli gospodarz wygral
    #             hometeam.numberOfMatchesWon += 1
    #             guestteam.numberOfMatchesLost += 1
    #         elif self.homeGoals < self.guestGoals:  # jesli gosc wygral
    #             hometeam.numberOfMatchesLost += 1
    #             guestteam.numberOfMatchesWon += 1
    #
    #
    #
    #     else:
    #
    #         if self.homeGoals == self.guestGoals:  # jesli remis
    #             if homeGoals == guestGoals:
    #                 hometeam.numberOfDraws += 0
    #                 guestteam.numberOfDraws += 0
    #             elif homeGoals > guestGoals:
    #                 hometeam.numberOfMatchesWon -= 1
    #                 guestteam.numberOfMatchesLost -= 1
    #                 hometeam.numberOfDraws += 1
    #                 guestteam.numberOfDraws += 1
    #             elif homeGoals < guestGoals:
    #                 hometeam.numberOfMatchesLost -= 1
    #                 guestteam.numberOfMatchesWon -= 1
    #                 hometeam.numberOfDraws += 1
    #                 guestteam.numberOfDraws += 1
    #         elif self.homeGoals > self.guestGoals:  # jesli gospodarz wygral
    #             if homeGoals == guestGoals:
    #                 hometeam.numberOfDraws -= 1
    #                 guestteam.numberOfDraws -= 1
    #                 hometeam.numberOfMatchesWon += 1
    #                 guestteam.numberOfMatchesLost += 1
    #             elif homeGoals > guestGoals:
    #                 hometeam.numberOfMatchesWon += 0
    #                 guestteam.numberOfMatchesLost += 0
    #             elif homeGoals < guestGoals:
    #                 hometeam.numberOfMatchesLost -= 1
    #                 guestteam.numberOfMatchesWon -= 1
    #                 hometeam.numberOfMatchesWon += 1
    #                 guestteam.numberOfMatchesLost += 1
    #         elif self.homeGoals < self.guestGoals:  # jesli gosc wygral
    #             if homeGoals == guestGoals:
    #                 hometeam.numberOfDraws -= 1
    #                 guestteam.numberOfDraws -= 1
    #                 hometeam.numberOfMatchesLost += 1
    #                 guestteam.numberOfMatchesWon += 1
    #             elif homeGoals > guestGoals:
    #                 hometeam.numberOfMatchesWon -= 1
    #                 guestteam.numberOfMatchesLost -= 1
    #                 hometeam.numberOfMatchesLost += 1
    #                 guestteam.numberOfMatchesWon += 1
    #             elif homeGoals < guestGoals:
    #                 hometeam.numberOfMatchesLost += 0
    #                 guestteam.numberOfMatchesWon += 0
    #
    #     hometeam.numberOfScores = 3 * hometeam.numberOfMatchesWon + 1 * hometeam.numberOfDraws
    #     guestteam.numberOfScores = 3 * guestteam.numberOfMatchesWon + 1 * guestteam.numberOfDraws
    #
    #     hometeam.save()
    #     guestteam.save()



class StatsPlayerMatch(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    idMatch = models.ForeignKey(Match, on_delete=models.CASCADE)
    numberOfYellowCard = models.PositiveIntegerField(default=0)
    numberOfGoals = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'idMatch'], name='ZAWODNIK_MECZ')
        ]
