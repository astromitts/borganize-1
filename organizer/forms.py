from django import forms
from django.forms import ModelForm, Textarea, CharField, ChoiceField
from organizer.models import KanBanItem, KanbanItemLabel, KanbanLabelColor

from organizer.utils import color_choice_tuples


class KanBanItemForm(ModelForm):
    new_label = CharField(required=False)
    new_label_color = ChoiceField(required=False, choices=KanbanLabelColor.choices_list())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(KanBanItemForm, self).__init__(*args, **kwargs)
        if self.user:
            LABEL_CHOICES = KanbanItemLabel.user_choices(self.user)
        else:
            LABEL_CHOICES = []
        self.fields['label'].choices = LABEL_CHOICES

    class Meta:
        model = KanBanItem
        fields = ['description', 'label', 'new_label', 'new_label_color']

class KanBanItemLabelForm(ModelForm):
    class Meta:
        model = KanbanItemLabel
        fields = ['label', 'color']

