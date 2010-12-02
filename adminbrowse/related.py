from django.contrib import admin
from django.utils.text import force_unicode
from django.utils.translation import ugettext as _
from django.db.models import FieldDoesNotExist
from django.core.urlresolvers import reverse

from adminbrowse.base import (ChangeListModelFieldColumn,
                              ChangeListTemplateColumn)


def admin_view_name(model_or_instance, short_name, site=admin.site):
    """
    Return the full name of the admin view given by `short_name` for
    the model given by `model_or_instance`. For example:

    >>> from django.contrib.auth.models import User
    >>> admin_view_name(User, 'changelist')
    'admin:auth_user_changelist'

    >>> from django.contrib.admin import AdminSite
    >>> test_site = AdminSite('test')
    >>> admin_view_name(User, 'change', site=test_site)
    'test:auth_user_change'

    """
    opts = model_or_instance._meta
    app_label, module_name = opts.app_label, opts.module_name
    return '%s:%s_%s_%s' % (site.name, app_label, module_name, short_name)


class ChangeLink(ChangeListTemplateColumn, ChangeListModelFieldColumn):
    """
    Changelist column that adds a link to the change view of the object in the
    specified foreign key field.

    If an instance's foreign key field is empty, the column will display the
    value of `default`, which defaults to the empty string.

    Include the `adminbrowse` CSS file in the ModelAdmin's `Media` definition
    to apply default styles to the link.

    This class is aliased as `adminbrowse.link_to_change` for better
    readability in `ModelAdmin` code.

    """
    template_name = "adminbrowse/link_to_change.html"

    def __init__(self, model, name, short_description=None, default="",
                 template_name=None, extra_context=None):
        ChangeListTemplateColumn.__init__(self, short_description,
                                          template_name or self.template_name,
                                          extra_context, name)
        ChangeListModelFieldColumn.__init__(self, model, name,
                                            short_description, default)
        self.to_model = self.field.rel.to
        self.to_opts = self.to_model._meta
        self.to_field = self.field.rel.field_name

    def get_context(self, obj):
        value  = getattr(obj, self.field_name)
        if value is not None:
            url = self.get_change_url(obj, value)
            title = self.get_title(obj, value)
        else:
            url = title = None
        context = {'column': self, 'object': obj, 'value': value, 'url': url,
                   'title': title}
        context.update(self.extra_context)
        return context

    def get_change_url(self, obj, value):
        view_name = admin_view_name(value, 'change')
        return reverse(view_name, args=[value.pk])

    def get_title(self, obj, value):
        strings = {'field_verbose_name': self.field.verbose_name}
        return _("Go to %(field_verbose_name)s") % strings

class RelatedList(ChangeListModelFieldColumn):
    """
    Changelist column that displays a textual list of the related objects
    in the specified many-to-many or one-to-many field.

    If an instance's has no related objects for the given field, the column
    will display the value of `default`, which defaults to the empty string.

    The `sep` argument specifies the separator to place between the string
    representation of each object.

    This class is aliased as `adminbrowse.related_list` for better
    readability in `ModelAdmin` code.

    """

    def __init__(self, model, name, short_description=None, default="",
                 sep=", "):
        ChangeListModelFieldColumn.__init__(self, model, name,
                                            short_description, default)
        if self.direct:
            self.to_model = self.field.related.parent_model
            self.to_opts = self.to_model._meta
            self.reverse_name = self.field.rel.related_name
            self.rel_name = self.opts.pk.name
        else:
            self.to_model = self.field.model
            self.to_opts = self.field.opts
            self.reverse_name = self.field.name
            if self.m2m:
                self.rel_name = self.field.rel.get_related_field().name
            else:
                self.rel_name = self.field.rel.field_name
        self.sep = sep

    def __call__(self, obj):
        related = getattr(obj, self.field_name).all()
        if related:
            return self.sep.join(map(force_unicode, related))
        else:
            return self.default

class ChangeListLink(ChangeListTemplateColumn, ChangeListModelFieldColumn):
    """
    Changelist column that adds a link to a changelist view containing only
    the related objects in the specified many-to-many or one-to-many field.

    The `text` argument sets the link text. If `text` is a callabe, it will
    be called with the (unevaluated) `QuerySet` for the related objects. If
    `text` is False in a boolean context ("", 0, etc.), the value of `default`
    will be rendered instead of the link. The default `text` returns the
    number of items in the `QuerySet`, so no link will be displayed if there
    are no related objects.

    Include the `adminbrowse` CSS file in the ModelAdmin's `Media` definition
    to apply default styles to the link.

    This class is aliased as `adminbrowse.link_to_changelist` for better
    readability in `ModelAdmin` code.

    """
    template_name = "adminbrowse/link_to_changelist.html"

    def __init__(self, model, name, short_description=None, text=len,
                 default="", template_name=None, extra_context=None):
        ChangeListTemplateColumn.__init__(self, short_description,
                                          template_name or self.template_name,
                                          extra_context)
        ChangeListModelFieldColumn.__init__(self, model, name,
                                            short_description, default)
        if self.direct:
            self.to_model = self.field.related.parent_model
            self.to_opts = self.to_model._meta
            self.reverse_name = self.field.rel.related_name
            self.rel_name = self.opts.pk.name
        else:
            self.to_model = self.field.model
            self.to_opts = self.field.opts
            self.reverse_name = self.field.name
            if self.m2m:
                self.rel_name = self.field.rel.get_related_field().name
            else:
                self.rel_name = self.field.rel.field_name
        self.text = text

    def get_context(self, obj):
        value  = getattr(obj, self.field_name).all()
        text = self.text
        if callable(text):
            text = text(value)
        if text:
            url = self.get_changelist_url(obj, value)
            title = self.get_title(obj, value)
        else:
            url = title = None
        context = {'column': self, 'object': obj, 'value': value,
                   'text': text, 'url': url, 'title': title}
        context.update(self.extra_context)
        return context

    def get_changelist_url(self, obj, value):
        view_name = admin_view_name(self.to_model, 'changelist')
        lookup_kwarg = '%s__%s__exact' % (self.reverse_name, self.rel_name)
        lookup_id = getattr(obj, self.rel_name)
        return reverse(view_name) + '?%s=%s' % (lookup_kwarg, lookup_id)

    def get_title(self, obj, value):
        strings = {
            'related_verbose_name_plural': self.to_opts.verbose_name_plural,
            'object_verbose_name': self.opts.verbose_name if self.m2m else
                                   self.field.verbose_name}
        return _("List %(related_verbose_name_plural)s with this "
                 "%(object_verbose_name)s") % strings

link_to_change = ChangeLink
link_to_changelist = ChangeListLink
related_list = RelatedList

