from django import forms
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.contrib.admin.widgets import FilteredSelectMultiple

from django.contrib.auth.models import User
from core.fields import HtmlSanitizedCharField
from events.models import Event, Occurrence, Category, Source
from importer.models import ExternalCategory
from events.utils import CachedCategoryTree
import pundit

# ==============
# = Base Forms =
# ==============
class EventForm(forms.ModelForm):
    class Meta:
        model = Event

class OccurrenceForm(forms.ModelForm):
    class Meta:
        model = Occurrence
        # start_datetime is a composite field of start_date and start_time
        # FIXME perhaps, it should be a db trigger instead of overridden save()
        exclude = ('start_datetime',)

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
    description = HtmlSanitizedCharField(required=False)
    # FIXME needs to be lazy loaded - otherwise, shit happens at import time
    # UPDATE: ugly fix
    @property
    def arbiter(self):
        if not hasattr(EventImportForm, '_arbiter'):
            setattr(EventImportForm, '_arbiter',
                pundit.Arbiter((
                        pundit.SourceCategoryRule(),
                        pundit.SourceRule()
                ))
            )
        return getattr(EventImportForm, '_arbiter')

    @property
    def importer_user(self):
        if not hasattr(EventImportForm, '_importer_user'):
            setattr(EventImportForm, '_importer_user',
                User.objects.get(username='importer')
            )
        return getattr(EventImportForm, '_importer_user')

    slug = forms.SlugField(required=False)
    popularity_score = forms.IntegerField(required=False)
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

    def clean(self):
        cleaned_data = super(EventImportForm, self).clean()

        # slug
        title = cleaned_data.get('title')
        if not title:
            raise ValidationError("'title' is required.")
        cleaned_data['title'] = self.fields['title'].clean(title)
        slug_value = slugify(title)[:50]
        cleaned_data['slug'] = self.fields['slug'].clean(slug_value)

        # sumbmitted_by
        cleaned_data['submitted_by'] = self.fields['submitted_by'].clean(self.importer_user)

        # is_active
        cleaned_data['is_active'] = self.fields['is_active'].clean(True)

        # concrete category :: via pundit
        event = self.instance
        source, external_categories= map(cleaned_data.get, ('source', 'external_categories'))
        if not source:
            raise ValidationError("'source' is required.")
        if not external_categories:
            raise ValidationError("'external_categories' is required.")
        concrete_category_value = self.arbiter.concrete_categories(event, source, external_categories)
        concrete_category_value_id = concrete_category_value and concrete_category_value.id or None
        cleaned_data['concrete_category'] = self.fields['concrete_category'].clean(concrete_category_value_id)

        # popularity score
        popularity_score = cleaned_data.get('popularity_score')
        popularity_score_value = popularity_score and int(popularity_score) or 0
        cleaned_data['popularity_score'] = self.fields['popularity_score'].clean(popularity_score_value)

        return cleaned_data

class OccurrenceImportForm(OccurrenceForm):
    pass
