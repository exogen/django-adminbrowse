# -*- coding: utf-8 -*-
from django.utils.text import force_unicode
from django.utils.translation import ugettext as _

from adminbrowse.base import ChangeListModelFieldColumn


class URLColumn(ChangeListModelFieldColumn):
    """Changelist column that links to the URL from the specified field.

    `model` is the model class for which a changelist is being rendered,
    and `name` is the name of the field containing a URL. If not provided,
    `short_description` will be set to the field's `verbose_name`.

    If an instance's URL field is empty, the column will display the value
    of `default`, which defaults to the empty string.

    The rendered link will have class="..." and target="..." attributes
    defined by the `target` and `classes` arguments, which default to
    '_blank' and 'external', respectively. Include the `adminbrowse`
    CSS file in the ModelAdmin's `Media` definition to style this default
    class with an "external link" icon.

    This class is aliased as `adminbrowse.link_to_url` for better readability
    in `ModelAdmin` code.

    """
    allow_tags = True

    def __init__(self, model, name, short_description=None, default="",
                 target='_blank', classes='external'):
        ChangeListModelFieldColumn.__init__(self, model, name,
                                            short_description, default)
        self.target = target
        if isinstance(classes, basestring):
            classes = classes.split()
        self.classes = list(classes)

    def __call__(self, obj):
        value = getattr(obj, self.field_name)
        if value:
            title = self.get_title(obj, value)
            classes = " ".join(self.classes)
            html = '<a href="%s" target="%s" class="%s" title="%s">%s</a>'
            return html % (value, self.target, classes, title, value)
        else:
            return self.default

    def get_title(self, obj, value):
        if self.target == '_blank':
            return _("Open URL in a new window")
        else:
            return _("Open URL")

class TruncatedFieldColumn(ChangeListModelFieldColumn):
    """
    Changelist column that truncates the value of a field to the specified
    length.

    `model` is the model class for which a changelist is being rendered,
    and `name` is the name of the field to render. The string value of the
    field will be truncated to the length given by `max_length` (required).
    If not provided, `short_description` will be set to the field's
    `verbose_name`.

    If an instance's field is empty, the column will display the value of
    `default`, which defaults to the empty string.

    The `tail` argument specifies the final truncation string, and defaults to
    an ellipsis.

    This class is aliased as `adminbrowse.truncated_field` for better
    readability in `ModelAdmin` code.

    """
    def __init__(self, model, name, max_length, short_description=None,
                 default="", tail=u"…"):
        ChangeListModelFieldColumn.__init__(self, model, name,
                                            short_description, default)
        self.max_length = max_length
        self.tail = tail

    def __call__(self, obj):
        value = getattr(obj, self.field_name)
        if value:
            text = force_unicode(value)
            if len(text) > self.max_length:
                text = text[:self.max_length] + self.tail
            return text
        else:
            return self.default

