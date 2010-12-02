from django.contrib import admin
from django.template.loader import render_to_string
from django.db.models import FieldDoesNotExist
from django.utils.text import force_unicode


class ChangeListColumn(object):
    """Base class for changelist columns. Must be subclassed.

    Subclasses should initialize this class with the desired
    `short_description` and `admin_order_field`, if applicable.

    The only method that must be implemented is `__call__()`,
    which takes the object for which a changelist row is being rendered.
    If `__call__()` returns HTML content intended to be rendered, the
    class or instance should set `allow_tags` to True.

    """
    allow_tags = False

    def __init__(self, short_description, admin_order_field=None):
        self.short_description = short_description
        self.admin_order_field = admin_order_field

    def __call__(self, obj):
        raise NotImplementedError

class ChangeListTemplateColumn(ChangeListColumn):
    """Class for rendering changelist column content from a template.

    Instances should set `short_description` and `template_name`. If
    `template_name` is not provided in the constructor, it will be taken from
    the class member.
    
    The default template context contains two variables: `column` (the
    `ChangeListColumn` instance), and `object` (the object for which a
    changelist row is being rendered). Additional context variables may be
    added by setting `extra_context`.

    This class is aliased as `adminbrowse.template_column` for better
    readability in `ModelAdmin` code.

    """
    allow_tags = True
    extra_context = {}

    def __init__(self, short_description, template_name=None,
                 extra_context=None, admin_order_field=None):
        ChangeListColumn.__init__(self, short_description, admin_order_field)
        self.template_name = template_name or self.template_name
        self.extra_context = extra_context or self.extra_context

    def __call__(self, obj):
        context = self.get_context(obj)
        return render_to_string(self.template_name, context)

    def get_context(self, obj):
        context = {'column': self, 'object': obj}
        context.update(self.extra_context)
        return context

class ChangeListModelFieldColumn(ChangeListColumn):
    def __init__(self, model, name, short_description=None, default=""):
        ChangeListColumn.__init__(self, short_description, None)
        self.field_name = name
        try:
            field, model_, self.direct, self.m2m = \
                model._meta.get_field_by_name(name)
        except FieldDoesNotExist:
            descriptor = getattr(model, name)
            field = descriptor.related
            self.direct = False
            self.m2m = True
        if self.direct:
            self.field = field
            self.model = field.model
            self.opts = self.model._meta
            if not self.m2m:
                self.admin_order_field = name
        else:
            self.field = field.field
            self.model = field.parent_model
            self.opts = field.parent_model._meta
        if self.short_description is None:
            if self.direct:
                self.short_description = force_unicode(field.verbose_name)
            else:
                self.short_description = force_unicode(name.replace('_', ' '))
        self.default = default

    def __call__(self, obj):
        value = getattr(obj, self.field_name)
        if value is not None:
            return force_unicode(value)
        else:
            return self.default

template_column = ChangeListTemplateColumn
model_field = ChangeListModelFieldColumn

