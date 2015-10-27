from __future__ import unicode_literals

from django.core.checks import Error
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import CharField, NOT_PROVIDED

from . import forms, widgets, Color, smart_hex


class ColorDescriptor(object):
    DEFAULT_COLOR = '#000000'

    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))

        color_hex_value = instance.__dict__[self.field.name]
        if not color_hex_value:
            if self.field.colors:
                color_hex_value = self.field.colors[0]
            elif self.field.default is not NOT_PROVIDED:
                color_hex_value = self.field.default
            else:
                color_hex_value = self.DEFAULT_COLOR
        return Color(hex=color_hex_value)

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = smart_hex(value or self.DEFAULT_COLOR)


class RGBColorField(CharField):
    """Field for database models"""
    widget = widgets.ColorFieldWidget
    default_validators = [RegexValidator(regex=forms.RGB_REGEX)]

    descriptor_class = ColorDescriptor

    def __init__(self, verbose_name=None, colors=None, *args, **kwargs):
        self.colors = colors
        kwargs['max_length'] = 7
        super(RGBColorField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs.update({
            'form_class': forms.RGBColorField,
            'widget': self.widget(colors=self.colors),
        })
        return super(RGBColorField, self).formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(RGBColorField, self).deconstruct()
        if self.colors is not None:
            kwargs['colors'] = self.colors
        del kwargs['max_length']
        return name, path, args, kwargs

    def check(self, **kwargs):
        errors = super(RGBColorField, self).check(**kwargs)
        if self.colors is not None:
            if not isinstance(self.colors, (list, tuple)):
                errors.append(Error(
                    'colors is not iterable',
                    hint='Define the colors param as list of strings.',
                    obj=self,
                    id='colorful.E001'
                ))
            else:
                try:
                    for color in self.colors:
                        self.clean(color, None)
                except ValidationError:
                    errors.append(Error(
                        'colors item validation error',
                        hint='Each item of the colors param must be a valid '
                             'color string itself.',
                        obj=self,
                        id='colorful.E002'
                    ))
        return errors

    def contribute_to_class(self, cls, name, **kwargs):
        super(RGBColorField, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.descriptor_class(self))

    # def pre_save(self, model_instance, add):
    #     return smart_hex(getattr(model_instance, self.attname))

    # def get_prep_value(self, value):
    #     value = super(RGBColorField, self).get_prep_value(value)
    #     return smart_hex(value)

    def to_python(self, value):
        return super(RGBColorField, self).to_python(smart_hex(value))

    # def bound_data(self, data, initial):
    #     return super(RGBColorField, self).bound_data(smart_hex(data), smart_hex(initial))

