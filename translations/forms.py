"""This module contains forms used for admin integration."""
import copy

from django.db.models.base import ModelBase
from django.forms import (CharField, BaseModelForm)
from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.models import ModelFormMetaclass, fields_for_model

from .models import Translation


class TranslatableFieldsMetaclass(DeclarativeFieldsMetaclass):
    """Collect Translantable Fields from translantable model."""

    def __new__(mcs, name, bases, attrs):
        new_class = super(TranslatableFieldsMetaclass, mcs).__new__(mcs, name, bases, attrs)

        translatable_model = attrs.get('translatable_model', None)

        if translatable_model == (ModelBase,):
            return new_class

        if translatable_model is not None:
            base_formfield_callback = None
            for b in bases:
                if hasattr(b, 'Meta') and hasattr(b.Meta, 'formfield_callback'):
                    base_formfield_callback = b.Meta.formfield_callback
                    break

            formfield_callback = attrs.pop('formfield_callback', base_formfield_callback)
            translatable_fields = translatable_model._get_translatable_fields_names()

            fields = fields_for_model(translatable_model,
                                      fields=translatable_fields,
                                      formfield_callback=formfield_callback,
                                      apply_limit_choices_to=False,
                                      )

            # translatable_model, opts.fields, opts.exclude, opts.widgets,
            # formfield_callback, opts.localized_fields, opts.labels,
            # opts.help_texts, opts.error_messages, opts.field_classes,
            # # limit_choices_to will be applied during ModelForm.__init__().
            # apply_limit_choices_to=False,

            declared_fields = copy.deepcopy(new_class.declared_fields)
            declared_fields.update(fields)

            new_class.base_fields = declared_fields
            new_class.declared_fields = declared_fields

        return new_class


class TranslateModelFormMetaclass(TranslatableFieldsMetaclass, ModelFormMetaclass):
    pass


def generate_translation_form(translatable):
    class TranslatableModelForm(BaseModelForm, metaclass=TranslateModelFormMetaclass):
        model = Translation
        translatable_model = translatable

        def __init__(self, data=None, *args, **kwargs):
            super(TranslatableModelForm, self).__init__(data, *args, **kwargs)

            if hasattr(self, 'instance'):
                for field in self.declared_fields.keys():
                    self.initial[field] = self.instance.data.get(field, None)

        def save(self, commit=True):
            for field in self.declared_fields.keys():
                value = self.cleaned_data.get(field, None)
                if value is not None:
                    self.instance.data.update({field: value})

            return super(TranslatableModelForm, self).save(commit)

    return TranslatableModelForm
