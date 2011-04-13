from django import forms
from django.template.defaultfilters import slugify
from django.contrib.admin.widgets import FilteredSelectMultiple

from events.models import Event, Occurrence, Category, Source
from events.utils import CachedCategoryTree

# ==============
# = Base Forms =
# ==============
class EventForm(forms.ModelForm):
    class Meta:
        model = Event

class OccurrenceForm(forms.ModelForm):
    class Meta:
        model = Occurrence

# ===============
# = Admin Forms =
# ===============
class CategoryAdminForm(forms.ModelForm):
    color = forms.RegexField(regex=r'^#(?:[0-9a-fA-F]{3}){1,2}$', required=False)

    class Meta:
        model = Category

    def save(self, commit=True):
        self.instance.slug = slugify(self.cleaned_data['title'])

        ctree = CachedCategoryTree()

        # get category_type from the parent
        parent = self.cleaned_data.get('parent')
        if parent:
            if parent == ctree.abstract_node: category_type = 'A'
            elif parent == ctree.concrete_node: category_type = 'C'
            else: category_type = parent.category_type
        else:
            category_type = 'O'
        self.instance.category_type = category_type

        # recurse the children and set their type correctly
        if self.instance.id:
            for c in ctree.children_recursive(self.instance):
                c.category_type = self.instance.category_type
                c.save()

        return super(CategoryAdminForm, self).save(commit=commit)

class EventAdminForm(EventForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.abstract.all(),
        widget=FilteredSelectMultiple(u'abstract categories', is_stacked=False),
        required=False
    )

class SourceAdminForm(forms.ModelForm):
    default_concrete_category = forms.ModelChoiceField(
        queryset=Category.concrete.all()
    )
    default_abstract_categories = forms.ModelMultipleChoiceField(
        queryset=Category.abstract.all(),
        widget=FilteredSelectMultiple(u'default abstract categories', is_stacked=False),
        required=False
    )

    class Meta:
        model = Source

# ================
# = Import Forms =
# ================
class EventImportForm(EventForm):
    slug = forms.SlugField(required=False)
    concrete_category = forms.ModelChoiceField(
        queryset=Category.concrete.all(), required=False,
        cache_choices=True
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.abstract.all(), required=False,
        cache_choices=True
    )
    # external_categories = forms.MultipleChoiceField()

    def clean_concrete_category(self):
        return Category.concrete.get(slug='movies')

    def clean_slug(self):
        title = self.cleaned_data['title']
        return slugify(title)[:50]

class OccurrenceImportForm(OccurrenceForm):
    pass