from django.contrib import admin
from django.urls import path, register_converter, include
from organizer.views import *
from organizer.url_converters import DateStrConverter
from django.views.generic import TemplateView

register_converter(DateStrConverter, 'dddddddd')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('login/', TemplateView.as_view(template_name='organizer/base.html'), name='login'),
    path('labels/', ManageLabels.as_view(), name='labels_list'),
    path('labels/add/', AddEditLabel.as_view(), name='create_label'),
    path('labels/edit/<int:label_id>/', AddEditLabel.as_view(), name='edit_label'),
    path('rollover/day/', RolloverView.as_view(), name='rollover_day'),
    path('kanbanitem/add/<int:organizerobject_id>/', AddItemView.as_view(), name='add_item'),
    path('kanbanitem/add/<int:organizerobject_id>/<int:kanbanitem_id>/', AddItemView.as_view(), name='add_item'),
    path('<str:item_type>/add/<int:organizerobject_id>/<str:datestr>/', AddItemView.as_view(), name='add_item'),
    path('kanban/<int:kanban_item_id>/<str:direction>/', MigrateKanbanItem.as_view(), name='migrate_kanban_item'),
    path('<str:datestr>/', Dashboard.as_view(), name='dashboard'),
    path('', Dashboard.as_view(), name='dashboard'),
]
