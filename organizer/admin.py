from django.contrib import admin
from organizer.models import (
    Month,
    Week,
    Day,
    KanBanItem,
    KanbanItemLabel,
    KanbanLabelColor,
)

admin.site.register(Month)
admin.site.register(Week)
admin.site.register(Day)
admin.site.register(KanBanItem)
admin.site.register(KanbanItemLabel)
admin.site.register(KanbanLabelColor)
