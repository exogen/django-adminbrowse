from django.contrib.admin import ModelAdmin
from django.db.models import FieldDoesNotExist, ForeignKey, URLField
from django.conf import settings

from adminbrowse.related import link_to_change
from adminbrowse.columns import link_to_url


class AutoBrowseModelAdmin(ModelAdmin):
    """
    Subclass this to automatically enable a subset of adminbrowse features:

    - Linking to the change form for `ForeignKey` fields.
    - Linking to the URL for `URLField` fields.

    This will also include the adminbrowse media definition.
    
    """
    def __init__(self, model, admin_site):
        super(AutoBrowseModelAdmin, self).__init__(model, admin_site)
        for i, name in enumerate(self.list_display):
            if isinstance(name, basestring):
                try:
                    field, model_, direct, m2m = \
                        self.opts.get_field_by_name(name)
                except FieldDoesNotExist:
                    pass
                else:
                    column = self._get_changelist_column(field)
                    if column is not None:
                        self.list_display[i] = column

    def _get_changelist_column(self, field):
        if isinstance(field, ForeignKey):
            return link_to_change(self.model, field.name)
        elif isinstance(field, URLField):
            return link_to_url(self.model, field.name)

    class Media:
        css = {'all': (settings.ADMINBROWSE_MEDIA_URL +
                       'css/adminbrowse.css',)}

