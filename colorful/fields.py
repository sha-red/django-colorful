from __future__ import unicode_literals

# FIXME Use dummy color class if colorutils is not available
from colorutils import Color

from django.core.checks import Error
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import CharField

from . import forms, widgets


class ColorDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, verbose_name=None, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))

        color_hex_value = instance.__dict__[self.field.name]
        return Color(hex=color_hex_value)

    def __set__(self, obj, value):
        if isinstance(value, Color):
            obj.__dict__[self.field.name] = value.hex
        else:
            obj.__dict__[self.field.name] = value


class RGBColorField(CharField):
    """Field for database models"""
    widget = widgets.ColorFieldWidget
    default_validators = [RegexValidator(regex=forms.RGB_REGEX)]

    descriptor_class = ColorDescriptor

    def __init__(self, colors=None, *args, **kwargs):
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
