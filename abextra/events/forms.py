from django import forms
from django.template.defaultfilters import slugify
from django.contrib.admin.widgets import FilteredSelectMultiple

from events.models import Event, Occurrence, Category, Source
from importer.models import ExternalCategory
from events.utils import CachedCategoryTree
from pundit import default_arbiter

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
    external_categories = forms.ModelMultipleChoiceField(
        queryset=ExternalCategory.objects.all(), required=False,
        cache_choices=True
    )
    source = forms.ModelChoiceField(
        queryset=Source.objects.all(),
        cache_choices=True,
        to_field_name='name'
    )

    def clean_slug(self):
        title = self.cleaned_data['title']
        return slugify(title)[:50]

    # def clean_concrete_category(self):
    #     return Category.concrete.get(id=2)

    def clean(self):
        event = self.instance
        source = self.cleaned_data['source'].name
        ext_category_ids = map(lambda c: c.xid, self.cleaned_data['external_categories'])
        concrete_category = default_arbiter \
            .concrete_categories(event, source, ext_category_ids)
        self.cleaned_data['concrete_category'] = concrete_category
        return self.cleaned_data

class OccurrenceImportForm(OccurrenceForm):
    pass