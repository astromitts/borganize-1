from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def pdb(item1, item2=None):
    import pdb
    pdb.set_trace()


@register.filter
def add_kanbanitem_url(objectid, datestr):
    if datestr:
        kwargs = {
            'organizerobject_id': objectid,
            'datestr': datestr
        }
    else:
        kwargs = {
            'organizerobject_id': objectid,
        }
    return reverse('add_item', kwargs=kwargs)
