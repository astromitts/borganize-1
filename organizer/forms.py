from django import forms
from django.forms import ModelForm, Textarea, CharField, ChoiceField
from organizer.models import KanBanItem, KanbanItemLabel, KanbanLabelColor
from django.db.utils import OperationalError

from organizer.utils import color_choice_tuples


class KanBanItemForm(ModelForm):
    new_label = CharField(required=False)
    new_label_color = ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(KanBanItemForm, self).__init__(*args, **kwargs)
        try:
            LABEL_CHOICES = KanbanItemLabel.user_choices(self.user)
        except OperationalError:
            LABEL_CHOICES = []

        try:
            LABEL_COLOR_CHOICES = KanbanLabelColor.choices_list()
        except OperationalError:
            LABEL_COLOR_CHOICES = []

        self.fields['label'].choices = LABEL_CHOICES
        self.fields['new_label_color'].choices = LABEL_COLOR_CHOICES

    class Meta:
        model = KanBanItem
        fields = ['description', 'label', 'new_label', 'new_label_color']

class KanBanItemLabelForm(ModelForm):
    class Meta:
        model = KanbanItemLabel
        fields = ['label', 'color']

