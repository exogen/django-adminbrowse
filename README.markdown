django-adminbrowse
==================
by [Brian Beck][www] / [@ua6oxa](http://twitter.com/ua6oxa)

![screenshot](http://exogen.github.com/django-adminbrowse/images/adminbrowse.png)

Make browsing the Django admin site easier by adding helpful features to
changelist pages.

* Link to the change form for foreign keys
* Link to changelist pages showing only related objects
* Link to URLs contained in URL fields
* Easily generate other dynamic changelist columns
* Works with no modifications to Django or its default templates

Installation
------------
From the Python package index:

    $ easy_install django-adminbrowse

From the source repository:

    $ pip install git+git://github.com/exogen/django-adminbrowse.git

See [INSTALL][] for more options.

Usage
-----
### Quickstart
To enable the most basic functionality, just inherit from
`adminbrowse.AutoBrowseModelAdmin` instead of Django's
`django.contrib.admin.ModelAdmin`. Make sure you have made adminbrowse media
available at the URL specified by the `ADMINBROWSE_MEDIA_URL` setting.

For example, if you copied the adminbrowse media to `<MEDIA_ROOT>/adminbrowse`,
set `ADMINBROWSE_MEDIA_URL` to `<MEDIA_URL>/adminbrowse/`.

### How it works
Django allows one to use callable objects in the `list_display` attribute of
`ModelAdmin` classes. adminbrowse is simply a collection of classes that
implement `__call__()` to dynamically render changelist column content.

The included `ModelAdmin` subclass, `AutoBrowseModelAdmin`, does only two
things:

* It scans the `list_display` attribute when instantiated, replacing field
  strings with their adminbrowse-enhanced equivalents when possible.
* It includes the adminbrowse CSS in its Media definition.

Documentation
-------------
### Example
Given these classes:

    class Author(Model):
        name = CharField(max_length=75)
        website = URLField(blank=True)

    class Book(Model):
        title = CharField(max_length=200)
        author = ForeignKey(Author, related_name='books')


`Author`'s `ModelAdmin.list_display` might find these useful:

* `link_to_url(Author, 'website')`: Make the author's URL clickable, if it exists
* `link_to_changelist(Author, 'books')`: Link to a filtered `Book` changelist showing
  only books for the appropriate author

And `Book`'s `ModelAdmin.list_display` might want to use these:
    
* `truncated_field(Book, 'title', 50)`: Truncate long titles to 50 characters,
  appending an ellipsis if needed
* `link_to_change(Book, 'author')`: Link to the change form of the book's author

### Media
If you're not using `AutoBrowseModelAdmin` to automatically include the adminbrowse
media, you'll want to place the following `Media` definition in your `ModelAdmin`
classes:

    class Media:
        css = {'all': (ADMINBROWSE_MEDIA_URL + 'css/adminbrowse.css',)}

...where `ADMINBROWSE_MEDIA_URL` is the value from `settings.py`.

### Performance effects
Won't using `link_to_changelist()` drastically increase the number of queries
executed? By default, yes, it will trigger one query per row in the changelist.
This trade-off may be acceptable, especially when you consider that the admin
site is paginated, and probably only accessed by a handful of people.

However, if you can't spare the extra queries, you can still use
`link_to_changelist()` in useful way. The `text` argument sets the link text
to display. If you set this to a string instead of a callable, the `QuerySet`
will never be evaluated (the default is `len()`, which is why the number of
items is shown -- it's called with the `QuerySet`).

Using it like so:

    link_to_changelist(Author, 'books', text="List books by this author")

...will still provide a clickable link to the filtered changelist without
performing the 'books' query.

[INSTALL]: http://github.com/exogen/django-adminbrowse/blob/master/INSTALL
[www]: http://brianbeck.com/

