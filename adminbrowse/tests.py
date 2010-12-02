# -*- coding: utf-8 -*-
from django.test import TestCase
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry
from django.conf.urls.defaults import *
from django.core.management import call_command

from adminbrowse import (link_to_change, link_to_changelist, related_list,
                         link_to_url, truncated_field)


# Test models that will give the functionality under test good coverage.

class Person(models.Model):
    pid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=75)
    website = models.URLField("home page", blank=True)

    class Meta:
        app_label = 'adminbrowse'

    def __unicode__(self):
        return self.name

class Genre(models.Model):
    gid = models.AutoField(primary_key=True)
    label = models.CharField(max_length=75)

    class Meta:
        app_label = 'adminbrowse'

    def __unicode__(self):
        return self.label

class Book(models.Model):
    bid = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Person, null=True, related_name='bibliography')
    categories = models.ManyToManyField(Genre, related_name='collection')

    class Meta:
        app_label = 'adminbrowse'

    def __unicode__(self):
        return self.title

test_site = admin.AdminSite('test')
test_site.register(Person)
test_site.register(Genre)
test_site.register(Book)
test_site.register(User)
test_site.register(Group)
test_site.register(LogEntry)
# An atypical admin path for the test site.
urlpatterns = patterns('', (r'^foo/admin/bar/', include(test_site.urls)))

def setup_test_models(sender, **kwargs):
    import adminbrowse.models
    if sender is adminbrowse.models and not setup_test_models.done:
        setup_test_models.done = True
        for model in [Person, Genre, Book]:
            setattr(adminbrowse.models, model.__name__, model)
        call_command('syncdb')
setup_test_models.done = False
models.signals.post_syncdb.connect(setup_test_models)

class TestChangeLink(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.people = Person.objects.all()
        self.books = Book.objects.all()
        self.link = link_to_change(Book, 'author')

    def test_allow_tags_is_true(self):
        self.assertEqual(self.link.allow_tags, True)

    def test_admin_order_field_is_field_name(self):
        self.assertEqual(self.link.admin_order_field, 'author')

    def test_call_returns_html(self):
        url = "/foo/admin/bar/adminbrowse/person/2/"
        self.assertEqual(self.link(self.books[1]).strip(),
            '<span class="change-link"><a href="%s" title="Go to author"></a>'
            ' Ernest Hemingway</span>' % url)
        url = "/foo/admin/bar/adminbrowse/person/3/"
        self.assertEqual(self.link(self.books[3]).strip(),
            '<span class="change-link"><a href="%s" title="Go to author"></a>'
            ' Kurt Vonnegut</span>' % url)

    def test_short_description_defaults_to_verbose_name(self):
        self.assertEqual(self.link.short_description, u"author")

    def test_short_description_sets_short_description(self):
        link = link_to_change(Book, 'author', short_description="written by")
        self.assertEqual(link.short_description, "written by")

    def test_default_sets_html_for_empty_field(self):
        link = link_to_change(Book, 'author', default="Unknown author")
        self.assertEqual(link(self.books[5]).strip(), "Unknown author")

    def test_default_defaults_to_empty_string(self):
        self.assertEqual(self.link(self.books[5]).strip(), "")

class TestOneToManyChangeListLink(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.people = Person.objects.all()
        self.books = Book.objects.all()
        self.link = link_to_changelist(Person, 'bibliography')

    def test_allow_tags_is_true(self):
        self.assertEqual(self.link.allow_tags, True)

    def test_admin_order_field_is_none(self):
        self.assertEqual(self.link.admin_order_field, None)

    def test_call_returns_html(self):
        url = "/foo/admin/bar/adminbrowse/book/?author__pid__exact=2"
        title = "List books with this author"
        self.assertEqual(self.link(self.people[1]).strip(),
            '<span class="changelist-link"><a href="%s" title="%s">3</a>'
            '</span>' % (url, title))
        url = "/foo/admin/bar/adminbrowse/book/?author__pid__exact=3"
        title = "List books with this author"
        self.assertEqual(self.link(self.people[2]).strip(),
            '<span class="changelist-link"><a href="%s" title="%s">2</a>'
            '</span>' % (url, title))

    def test_short_description_defaults_to_field_name(self):
        self.assertEqual(self.link.short_description, u"bibliography")

    def test_short_description_sets_short_description(self):
        link = link_to_changelist(Person, 'bibliography', "novels")
        self.assertEqual(link.short_description, "novels")

    def test_text_sets_rendered_link_text(self):
        link = link_to_changelist(Person, 'bibliography',
                                  text="List bibliography")
        url = "/foo/admin/bar/adminbrowse/book/?author__pid__exact=3"
        title = "List books with this author"
        self.assertEqual(link(self.people[2]).strip(),
            '<span class="changelist-link"><a href="%s" title="%s">List'
            ' bibliography</a></span>' % (url, title))

    def test_callable_text_gets_called_with_value(self):
        link = link_to_changelist(Person, 'bibliography',
                                  text=lambda x: "List books (%s)" % len(x))
        url = "/foo/admin/bar/adminbrowse/book/?author__pid__exact=3"
        title = "List books with this author"
        self.assertEqual(link(self.people[2]).strip(),
            '<span class="changelist-link"><a href="%s" title="%s">List'
            ' books (2)</a></span>' % (url, title))

    def test_default_sets_html_for_empty_text(self):
        link = link_to_changelist(Person, 'bibliography', default="No books")
        self.assertEqual(link(self.people[0]).strip(), "No books")

    def test_html_for_empty_set_defaults_to_empty_string(self):
        self.assertEqual(self.link(self.people[0]).strip(), "")

    def test_html_for_empty_text_defauls_to_empty_string(self):
        link = link_to_changelist(Person, 'bibliography', text="")
        self.assertEqual(link(self.people[2]).strip(), "")

class TestIndirectManyToManyChangeListLink(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.genres = Genre.objects.all()
        self.books = Book.objects.all()
        self.link = link_to_changelist(Genre, 'collection')

    def test_allow_tags_is_true(self):
        self.assertEqual(self.link.allow_tags, True)

    def test_admin_order_field_is_none(self):
        self.assertEqual(self.link.admin_order_field, None)

    def test_call_returns_html(self):
        url = "/foo/admin/bar/adminbrowse/book/?categories__gid__exact=1"
        title = "List books with this genre"
        self.assertEqual(self.link(self.genres[0]).strip(),
            '<span class="changelist-link"><a href="%s" title="%s">3</a>'
            '</span>' % (url, title))

    def test_short_description_defaults_to_field_name(self):
        self.assertEqual(self.link.short_description, u"collection")

    def test_short_description_sets_short_description(self):
        link = link_to_changelist(Genre, 'collection', "novels")
        self.assertEqual(link.short_description, "novels")

    def test_html_for_empty_set_defaults_to_empty_string(self):
        self.assertEqual(self.link(self.genres[4]).strip(), "")

    def test_default_sets_html_for_empty_set(self):
        link = link_to_changelist(Genre, 'collection', default="No books")
        self.assertEqual(link(self.genres[4]).strip(), "No books")

    def test_default_defaults_to_empty_string(self):
        self.assertEqual(self.link(self.genres[4]).strip(), "")

class TestDefaultRelatedNameChangeListLink(TestCase):
    def setUp(self):
        self.one_to_many = link_to_changelist(User, 'logentry_set')
        self.many_to_many = link_to_changelist(Group, 'user_set')

    def test_short_description_is_accessor_with_spaces(self):
        self.assertEqual(self.one_to_many.short_description, u"logentry set")
        self.assertEqual(self.many_to_many.short_description, u"user set")

class TestDirectManyToManyChangeListLink(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.genres = Genre.objects.all()
        self.books = Book.objects.all()
        self.link = link_to_changelist(Book, 'categories')

    def test_allow_tags_is_true(self):
        self.assertEqual(self.link.allow_tags, True)

    def test_admin_order_field_is_none(self):
        self.assertEqual(self.link.admin_order_field, None)

    def test_call_returns_html(self):
        url = "/foo/admin/bar/adminbrowse/genre/?collection__bid__exact=5"
        title = "List genres with this book"
        self.assertEqual(self.link(self.books[4]).strip(),
            '<span class="changelist-link"><a href="%s" title="%s">2</a>'
            '</span>' % (url, title))

    def test_short_description_defaults_to_verbose_name(self):
        self.assertEqual(self.link.short_description, u"categories")

    def test_short_description_sets_short_description(self):
        link = link_to_changelist(Book, 'categories', "genres")
        self.assertEqual(link.short_description, "genres")

    def test_html_for_empty_set_defaults_to_empty_string(self):
        self.assertEqual(self.link(self.books[5]).strip(), "")

    def test_default_sets_html_for_empty_set(self):
        link = link_to_changelist(Book, 'categories', default="No genres")
        self.assertEqual(link(self.books[5]).strip(), "No genres")

class TestOneToManyRelatedList(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.people = Person.objects.all()
        self.books = Book.objects.all()
        self.column = related_list(Person, 'bibliography')

    def test_allow_tags_is_false(self):
        self.assertEqual(self.column.allow_tags, False)

    def test_admin_order_field_is_none(self):
        self.assertEqual(self.column.admin_order_field, None)

    def test_short_description_defaults_to_field_name(self):
        self.assertEqual(self.column.short_description, u"bibliography")

    def test_call_returns_comma_separated_list(self):
        self.assertEqual(self.column(self.people[2]),
            "Cat's Cradle, Slaughterhouse-Five")

    def test_default_sets_text_for_empty_set(self):
        column = related_list(Person, 'bibliography', default="No books")
        self.assertEqual(column(self.people[0]), "No books")

    def test_sep_sets_string_separator(self):
        column = related_list(Person, 'bibliography', sep=" ~ ")
        self.assertEqual(column(self.people[2]),
            "Cat's Cradle ~ Slaughterhouse-Five")

class TestDirectManyToManyRelatedList(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.genres = Genre.objects.all()
        self.books = Book.objects.all()
        self.column = related_list(Book, 'categories')

    def test_allow_tags_is_false(self):
        self.assertEqual(self.column.allow_tags, False)

    def test_admin_order_field_is_none(self):
        self.assertEqual(self.column.admin_order_field, None)

    def test_call_returns_comma_separated_list(self):
        self.assertEqual(self.column(self.books[4]), "War, Science Fiction")

class TestIndirectManyToManyRelatedList(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.genres = Genre.objects.all()
        self.books = Book.objects.all()
        self.column = related_list(Genre, 'collection')

    def test_allow_tags_is_false(self):
        self.assertEqual(self.column.allow_tags, False)

    def test_admin_order_field_is_none(self):
        self.assertEqual(self.column.admin_order_field, None)

    def test_call_returns_comma_separated_list(self):
        self.assertEqual(self.column(self.genres[1]),
            "The Old Man and the Sea")

class TestURLColumn(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.people = Person.objects.all()
        self.column = link_to_url(Person, 'website')

    def test_allow_tags_is_true(self):
        self.assertEqual(self.column.allow_tags, True)

    def test_short_description_defaults_to_verbose_name(self):
        self.assertEqual(self.column.short_description, "home page")

    def test_short_description_sets_short_description(self):
        column = link_to_url(Person, 'website', "homepage URL")
        self.assertEqual(column.short_description, "homepage URL")

    def test_admin_order_field_is_field_name(self):
        self.assertEqual(self.column.admin_order_field, 'website')

    def test_call_returns_link_html(self):
        self.assertEqual(self.column(self.people[0]),
            '<a href="http://example.com/twain" target="_blank"'
            ' class="external" title="Open URL in a new window">'
            'http://example.com/twain</a>')
    
    def test_target_sets_link_target(self):
        column = link_to_url(Person, 'website', target="test")
        self.assertEqual(column(self.people[0]),
            '<a href="http://example.com/twain" target="test"'
            ' class="external" title="Open URL">http://example.com/twain</a>')

    def test_classes_sets_link_class(self):
        column = link_to_url(Person, 'website', classes=['one', 'two'])
        self.assertEqual(column(self.people[0]),
            '<a href="http://example.com/twain" target="_blank"'
            ' class="one two" title="Open URL in a new window">'
            'http://example.com/twain</a>')

    def test_default_sets_html_for_empty_field(self):
        column = link_to_url(Person, 'website', default="No website")
        self.assertEqual(column(self.people[1]), "No website")

    def test_default_defaults_to_empty_string(self):
        self.assertEqual(self.column(self.people[1]), "")

class TestTruncatedTextColumn(TestCase):
    urls = 'adminbrowse.tests'
    fixtures = ['test_adminbrowse.json']

    def setUp(self):
        self.people = Person.objects.all()
        self.column = truncated_field(Person, 'website', 24)

    def test_allow_tags_is_false(self):
        self.assertEqual(self.column.allow_tags, False)

    def test_short_description_defaults_to_verbose_name(self):
        self.assertEqual(self.column.short_description, "home page")

    def test_call_returns_text_truncated_to_max_length(self):
        self.assertEqual(self.column(self.people[2]),
            u"http://example.com/vonne…")
        self.assertEqual(self.column(self.people[0]),
            u"http://example.com/twain")

    def test_max_length_sets_length_before_truncation(self):
        column = truncated_field(Person, 'website', 8)
        self.assertEqual(column(self.people[0]), u"http://e…")

    def test_default_sets_text_for_empty_field(self):
        column = truncated_field(Person, 'website', 80, default="No website")
        self.assertEqual(column(self.people[1]), "No website")
    
    def test_default_defaults_to_empty_string(self):
        self.assertEqual(self.column(self.people[1]), "")

