from django.db import models
from datetime import datetime
import calendar
from django.contrib.auth.models import User

from organizer.utils import get_color_name, color_choice_tuples


class OrganizerItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def subclass_type(self):
        try:
            self.week
            return 'week'
        except OrganizerItem.week.RelatedObjectDoesNotExist:
            pass
        try:
            self.day
            return 'day'
        except OrganizerItem.day.RelatedObjectDoesNotExist:
            pass

        try:
            self.month
            return 'month'
        except OrganizerItem.month.RelatedObjectDoesNotExist:
            pass
        return None

    @property
    def subclass_model(self):
        if self.subclass_type == 'week':
            return Week
        elif self.subclass_type == 'month':
            return Month
        elif self.subclass_type == 'day':
            return Day
        return None


    @property
    def todo_items(self):
        return self.kanbanitem_set.all().filter(status='to do')

    @property
    def doing_items(self):
        return self.kanbanitem_set.all().filter(status='doing')

    @property
    def done_items(self):
        return self.kanbanitem_set.all().filter(status='done')

    @property
    def pending_items(self):
        unrolled_kanban_items = []
        previous_organizer_items = OrganizerItem.objects.filter(user=self.user).exclude(pk=self.pk).order_by('-pk')
        for poi in previous_organizer_items:
            unrolled_kanban_item_qs = poi.kanbanitem_set.filter(
                status__in=['to do', 'doing'],
                rollover_handled=False
            ).all()
            for unrolled_item in unrolled_kanban_item_qs:
                unrolled_kanban_items.append(unrolled_item)
        return unrolled_kanban_items


class KanbanLabelColor(models.Model):
    name = models.CharField(max_length=25, unique=True)
    hex_value = models.CharField(max_length=7, unique=True, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def choices_dict(cls):
        choices_dict = {}
        for color in cls.objects.all():
            choices_dict[color.name] = color.hex_value
        return choices_dict

    @classmethod
    def choices_list(cls):
        choices_list = []
        for color in cls.objects.all():
            choices_list.append((color.hex_value, color.name))
        return choices_list


class KanbanItemLabel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    # color = models.CharField(max_length=25, choices=color_choice_tuples())
    color = models.ForeignKey(KanbanLabelColor, blank=True, null=True, on_delete=models.SET_NULL)

    @property
    def color_name(self):
        return get_color_name(self.color)

    @classmethod
    def user_choices(cls, user):
        user_choices = []
        for label in cls.objects.filter(user=user).all():
            user_choices.append((label.pk, label.label))
        return user_choices


    def __str__(self):
        return self.label


class KanBanItem(models.Model):
    status_choices = [
        ('to do', 'to do'),
        ('doing', 'doing'),
        ('done', 'done'),
    ]

    description = models.TextField()
    rollover_count = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=status_choices, default='to do')
    organizer_item = models.ForeignKey(OrganizerItem, on_delete=models.CASCADE)
    rollover_handled = models.BooleanField(default=False)
    label = models.ForeignKey(KanbanItemLabel, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-pk']

    def advance(self):
        if self.status == 'to do':
            self.status = 'doing'
        elif self.status == 'doing':
            self.status = 'done'
        self.save()

    def reverse(self):
        if self.status == 'doing':
            self.status = 'to do'
        elif self.status == 'done':
            self.status = 'doing'
        self.save()

    def rollover(self, target_organizer_item):
        copied_item = KanBanItem(
            description=self.description,
            organizer_item=target_organizer_item,
            status=self.status,
            rollover_count=self.rollover_count + 1
        )
        copied_item.save()
        self.rollover_handled = True
        self.save()


    def ignore(self):
        self.rollover_handled = True
        self.save()

    def __str__(self):
        return '{} // {}'.format(self.organizer_item, self.description[:20])


class Month(OrganizerItem):
    month_name = models.CharField(max_length=25)
    month_number = models.IntegerField(
        choices=[
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (7, 7),
            (8, 8),
            (9, 9),
            (10, 10),
            (11, 11),
            (12, 12),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    year = models.IntegerField()

    @classmethod
    def get_or_create(cls, user, day):
        date = day.date
        created = False
        month_qs = cls.objects.filter(user=user, month_number=date.month)
        if month_qs.exists():
            month = month_qs.first()
            created = False
        else:
            month = cls(
                user=user,
                month_number=date.month,
                start_date=date.replace(day=1),
                end_date=date.replace(day=calendar.monthrange(date.year, date.month)[1]),
                month_name=calendar.month_name[date.month],
                year=date.year
            )
            month.save()
            created = True
        return month, created

    def __str__(self):
        return '{} // {}'.format(self.user, self.month_name)


class Week(OrganizerItem):
    week_number = models.IntegerField()

    def __str__(self):
        return '{} // week {}'.format(self.user, self.week_number)

    @classmethod
    def get_or_create(cls, user, day):
        date = day.date
        created = False
        week_number = date.isocalendar()[1]
        week_qs = cls.objects.filter(user=user, week_number=week_number)
        if week_qs.exists():
            week = week_qs.first()
            created = False
        else:
            week = cls(
                user=user,
                week_number=week_number,
            )
            week.save()
            created = True
        return week, created


class Day(OrganizerItem):
    date = models.DateField()

    def __str__(self):
        return '{} // {}'.format(self.user, self.date)

    @classmethod
    def get_or_create(cls, user, date):
        day_qs = cls.objects.filter(user=user, date=date)
        created = False
        if day_qs.exists():
            day = day_qs.first()
            created = False
        else:
            day = cls(user=user, date=date)
            day.save()
            created = True
        return day, created
