from django.contrib import admin
from django.contrib.contenttypes.admin import GenericInlineModelAdmin, GenericStackedInline, GenericTabularInline

from .models import Translation
from .forms import generate_translation_form


class TranslationInline(GenericInlineModelAdmin):
    ct_field = 'entity_type'
    ct_fk_field = 'entity_id'
    model = Translation
    exclude = ['data']
    extra = 1


class StackedTranslationInline(TranslationInline, GenericStackedInline):
    pass


class TabularTranslationInline(TranslationInline, GenericTabularInline):
    pass


class TranslatableAdmin(admin.ModelAdmin):
    inlines =[StackedTranslationInline]

    def get_inline_instances(self, request, obj=None):
        inlines = list(
            super(TranslatableAdmin, self).get_inline_instances(request, obj)
        )
        self.prepare_translation_inline(inlines, TranslationInline)
        return inlines

    def prepare_translation_inline(self, inlines, inline_type):
        form = generate_translation_form(self.model)
        for i, v in enumerate(inlines):
            if isinstance(v, inline_type):
                inlines[i].form = form
                break
