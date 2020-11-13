from django.template import loader
from django.http import HttpResponse
from django.views import View
from django.shortcuts import redirect, resolve_url, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth import logout
from django.urls import reverse
from urllib.parse import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from organizer.models import (
    Day,
    Month,
    Week,
    KanBanItem,
    OrganizerItem,
    KanbanItemLabel,
    KanbanLabelColor,
)

from organizer.forms import KanBanItemForm, KanBanItemLabelForm

from datetime import datetime, timedelta


def logout(request):
    logout(request)
    return redirect(reverse('login'))


class AuthenticatedAppView(View):
    """ Base class thay boots you from a view if you are not logged in
        also does some other variable assignments that are commonly required

        Wow LoginRequiredMixin was not working at all so I had to copy a bunch of it here :\
    """
    login_url = '/login/'
    permission_denied_message = 'Login required'
    raise_exception = False
    redirect_field_name = REDIRECT_FIELD_NAME

    def get_login_url(self):
        """
        Override this method to override the login_url attribute.
        """
        login_url = self.login_url or settings.LOGIN_URL
        if not login_url:
            raise ImproperlyConfigured(
                '{0} is missing the login_url attribute. Define {0}.login_url, settings.LOGIN_URL, or override '
                '{0}.get_login_url().'.format(self.__class__.__name__)
            )
        return str(login_url)


    def get_redirect_field_name(self):
        """
        Override this method to override the redirect_field_name attribute.
        """
        return self.redirect_field_name

    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.permission_denied_message)

        path = self.request.build_absolute_uri()
        resolved_login_url = resolve_url(self.get_login_url())
        # If the login url is the same scheme and net location then use the
        # path as the "next" url.
        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if (
            (not login_scheme or login_scheme == current_scheme) and
            (not login_netloc or login_netloc == current_netloc)
        ):
            path = self.request.get_full_path()
            return redirect_to_login(
                path,
                resolved_login_url,
                self.get_redirect_field_name(),
            )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def setup(self, request, *args, **kwargs):
        super(AuthenticatedAppView, self).setup(request, *args, **kwargs)

        if not request.user.is_authenticated:
            return self.handle_no_permission()
        try:
            self.appuser = User.objects.get(email=request.user.email)
        except ValueError:
            return self.handle_no_permission()

        if kwargs.get('organizerobject_id'):
            self.organizer_object = get_object_or_404(OrganizerItem, pk=kwargs['organizerobject_id'], user=self.appuser)

        if kwargs.get('kanbanitem_id'):
            self.kanban_item = get_object_or_404(KanBanItem, pk=kwargs['kanbanitem_id'])

        self.today = datetime.today()

        if kwargs.get('datestr'):
            self.datestr = kwargs['datestr']
            self.requested_date = datetime.strptime(self.datestr, '%Y%m%d')
            self.dashboard_url = reverse('dashboard', kwargs={'datestr': self.datestr})
        else:
            self.requested_date = self.today
            self.datestr = None
            self.dashboard_url = reverse('dashboard')

        self.context = {
            'date': self.requested_date,
            'datestr': self.datestr,
            'dashboard_url': self.dashboard_url
        }

    def set_dashboard_items(self):
        self.day, self.day_created = Day.get_or_create(user=self.appuser, date=self.requested_date)
        self.month, self.month_created = Month.get_or_create(user=self.appuser, day=self.day)
        self.week, self.week_created = Week.get_or_create(user=self.appuser, day=self.day)
        self.date = self.day.date
        if self.requested_date == self.today:
            pending_items = self.day.pending_items
            self.pending_items = {}
            for item in pending_items:
                this_category = None
                if item.organizer_item.subclass_type == 'day':
                    this_category = self.pending_items.get(
                        'day',
                        {
                            'header_title': 'To do today',
                            'items': [],
                            'organizerobject_id': self.day.pk
                        }
                    )
                elif item.organizer_item.subclass_type == 'week' and item.organizer_item.week != self.week:
                    this_category = self.pending_items.get(
                        'week',
                        {
                            'header_title': 'To do this week',
                            'items': [],
                            'organizerobject_id': self.week.pk
                        }
                    )
                elif item.organizer_item.subclass_type == 'month' and item.organizer_item.month != self.month:
                    this_category = self.pending_items.get(
                        'month',
                        {
                            'header_title': 'To do this month',
                            'items': [],
                            'organizerobject_id': self.month.pk
                        }
                    )
                if this_category:
                    this_category['items'].append(item)
                    self.pending_items[item.organizer_item.subclass_type] = this_category

        else:
            self.pending_items = None



class Dashboard(AuthenticatedAppView):

    def get(self, request, *args, **kwargs):
        template = loader.get_template('organizer/dashboard.html')
        self.set_dashboard_items()

        if self.pending_items:
            return redirect(reverse('rollover_day'))

        organizer_objects = [
            {
                'kanban_header': 'Today',
                'organizer_object': self.day
            },
            {
                'kanban_header': 'This week',
                'organizer_object': self.week
            },
            {
                'kanban_header': 'This month',
                'organizer_object': self.month
            }
        ]

        self.context.update({
            'organizer_objects': organizer_objects,
            'datestr': self.datestr,
            'date': self.day.date,
            'week_number': self.week.week_number
        })
        return HttpResponse(template.render(self.context, request))


class RolloverView(AuthenticatedAppView):
    def get(self, request, *args, **kwargs):
        self.set_dashboard_items()
        template = loader.get_template('organizer/rollover.html')
        if self.pending_items:
            self.context['rollover_categories'] = self.pending_items
            return HttpResponse(template.render(self.context, request))
        else:
            return redirect(reverse('dashboard'))

    def post(self, request, *args, **kwargs):
        rollover_items = []
        ignore_items = []
        for field, value in request.POST.items():
            if field.startswith('rollover_item'):
                item_ids = field.replace('rollover_item_', '').split('_')
                organizer_id = int(item_ids[0])
                item_id = int(item_ids[1])
                item_obj = KanBanItem.objects.get(pk=item_id)
                organizer_obj = OrganizerItem.objects.get(pk=organizer_id)
                if value == 'rollover':
                    item_obj.rollover(organizer_obj)
                else:
                    item_obj.ignore()
        return redirect(reverse('dashboard'))


class AddEditItemView(AuthenticatedAppView):
    def setup(self, request, *args, **kwargs):
        super(AddEditItemView, self).setup(request, *args, **kwargs)
        self.action = self.dashboard_url
        self.organizer_obj = OrganizerItem.objects.get(pk=kwargs['organizerobject_id'])
        self.template = loader.get_template('organizer/includes/form_include.html')
        if kwargs.get('kanbanitem_id'):
            self.edit_item = KanBanItem.objects.get(pk=kwargs['kanbanitem_id'])
        else:
            self.edit_item = None
        self.context['header'] = 'Add a new Kanban Item'


    def get(self, request, *args, **kwargs):
        if self.edit_item:
            form = KanBanItemForm(instance=self.edit_item, user=self.appuser)
        else:
            form = KanBanItemForm(user=self.appuser)
        self.context['form'] = form
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = KanBanItemForm(data=request.POST)
        if form.is_valid:
            if request.POST.get('new_label'):
                new_label = KanbanItemLabel(
                    label=request.POST['new_label'],
                    color=KanbanLabelColor.objects.get(hex_value=request.POST['new_label_color']),
                    user=self.appuser,
                )
                new_label.save()
                label = new_label
            else:
                label_id = request.POST.get('label')
                if label_id:
                    label = KanbanItemLabel.objects.get(pk=label_id)
                else:
                    label = None
            if self.edit_item:
                self.edit_item.organizer_item = self.organizer_obj
                self.edit_item.description = request.POST['description']
                self.edit_item.label=label
                self.edit_item.save()
            else:
                newitem = KanBanItem(organizer_item=self.organizer_obj, description=request.POST['description'], label=label)
                newitem.save()

            return redirect(self.dashboard_url)
        self.context['form'] = form
        return HttpResponse(self.template.render(self.context, request))


class ShiftKanbanItem(AuthenticatedAppView):
    def get(self, request, *args, **kwargs):
        self.set_dashboard_items()
        direction = kwargs['direction']
        if self.organizer_object.subclass_type == 'week':
            if direction == 'up':
                self.day.kanbanitem_set.add(self.kanban_item)
                self.day.save()
            elif direction == 'down':
                self.month.kanbanitem_set.add(self.kanban_item)
                self.month.save()
        elif self.organizer_object.subclass_type == 'month':
            if direction == 'up':
                self.week.kanbanitem_set.add(self.kanban_item)
                self.week.save()
        elif self.organizer_object.subclass_type == 'day':
            if direction == 'down':
                self.week.kanbanitem_set.add(self.kanban_item)
                self.week.save()
        return redirect(reverse('dashboard'))


class MigrateKanbanItem(AuthenticatedAppView):
    def get(self, request, *args, **kwargs):
        item = KanBanItem.objects.get(pk=kwargs['kanban_item_id'])
        if kwargs['direction'] == 'forward':
            item.advance()
        elif kwargs['direction'] == 'back':
            item.reverse()
        return redirect(reverse('dashboard'))


class ManageLabels(AuthenticatedAppView):
    def get(self, request, *args, **kwargs):
        self.template = loader.get_template('organizer/labels_list.html')
        labels = KanbanItemLabel.objects.filter(user=self.appuser)
        self.context.update({'labels': labels})
        return HttpResponse(self.template.render(self.context, request))


class AddEditLabel(AuthenticatedAppView):
    def setup(self, request, *args, **kwargs):
        super(AddEditLabel, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('organizer/includes/form_include.html')
        if kwargs.get('label_id'):
            self.edit_label = KanbanItemLabel.objects.get(pk=kwargs['label_id'])
            if self.edit_label.user != self.appuser:
                self.handle_no_permission()
        else:
            self.edit_label = None


    def get(self, request, *args, **kwargs):
        if self.edit_label:
            form = KanBanItemLabelForm(instance=self.edit_label)
        else:
            form = KanBanItemLabelForm()
        self.context['form'] = form
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = KanBanItemLabelForm(data=request.POST)
        if form.is_valid:
            if self.edit_label:
                self.edit_label.label = request.POST['label']
                self.edit_label.color = KanbanLabelColor.objects.get(pk=request.POST['color'])
                self.edit_label.save()

            else:
                new_label = KanbanItemLabel(
                    label=request.POST['label'],
                    color=KanbanLabelColor.objects.get(pk=request.POST['color']),
                    user=self.appuser
                )
                new_label.save()
            return redirect(reverse('labels_list'))
        else:
            return HttpResponse(self.template.render(self.context, request))
