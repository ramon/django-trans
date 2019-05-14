import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import get_language, gettext_lazy as _


class Translation(models.Model):
    class Meta:
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')

    LANGUAGES = list((t for t in settings.LANGUAGES if t[0] != settings.LANGUAGE_CODE))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.ForeignKey(ContentType, related_name='entities', on_delete=models.CASCADE)
    entity_id = models.UUIDField(db_index=True, null=False)
    entity = GenericForeignKey('entity_type', 'entity_id')

    lang_code = models.CharField(max_length=6, db_index=True, null=False, choices=LANGUAGES)
    data = JSONField(default=dict)
    created_on = models.DateTimeField(_('Created on'), auto_now_add=True, editable=False)
    updated_on = models.DateTimeField(_('Updated_on'), auto_now=True, editable=False)

    def __str__(self):
        return self.lang_code

    # def __getattr__(self, item):
    #     if self.data:
    #         return self.data[item] or None
    #
    #     return None

    # def __setattr__(self, key, value):
    #     self.data.update({key: value})


class TranslationProxy:
    class TranslationWrapper:
        def __init__(self, instance, locale):
            self.instance = instance
            try:
                self.translation = instance.translations.get(lang_code=locale)
            except Translation.DoesNotExist:
                self.translation = None

        def __getattr__(self, item):
            if all([
                item not in ['id', 'pk'],
                self.translation is not None,
                item in self.translation.data.keys()
            ]):
                return getattr(self.translation, item, getattr(self.instance, item))
            return getattr(self.instance, item)

    def __get__(self, instance, owner):
        locale = get_language()
        return self.TranslationWrapper(instance, locale)


class TranslationModelBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        super(TranslationModelBase, cls).__new__(cls, name, bases, attrs, **kwargs)


class TranslationMixin(models.Model):
    class Meta:
        abstract = True

    class TranslationMeta:
        fields = None
        exclude = []

    translations = GenericRelation(Translation, 'entity_id', 'entity_type')
    translated = TranslationProxy()

    def __init__(self, *args, **kwargs):
        super(TranslationMixin, self).__init__(*args, **kwargs)

    @classmethod
    def get_translatable_fields(cls):
        if not hasattr(cls, '_cached_translatable_fields'):
            if getattr(cls.TranslationMeta, 'fields', None) is None:
                fields = []
                for field in cls._meta.get_fields():
                    if isinstance(
                        field,
                        (models.CharField, models.TextField,)
                    ) and not isinstance(
                        field,
                        models.EmailField
                    ) and not (
                        hasattr(field, 'choices') and field.choices
                    ) and not (hasattr(cls.TranslationMeta, 'exclude') and field.name in cls.TranslationMeta.exclude):
                        fields.append(field)
            else:
                fields = [
                    cls._meta.get_field(field_name)
                    for field_name in cls.TranslationMeta.fields
                ]
            cls._cached_translatable_fields = fields
        return cls._cached_translatable_fields

    @classmethod
    def _get_translatable_fields_names(cls):
        """Return the names of the model's translatable fields."""
        if not hasattr(cls, '_cached_translatable_fields_names'):
            cls._cached_translatable_fields_names = [
                field.name for field in cls.get_translatable_fields()
            ]
        return cls._cached_translatable_fields_names
