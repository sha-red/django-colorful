# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# FIXME Use dummy color class if colorutils is not available
from colorutils import Color as ColorBase


class Color(ColorBase):
    def as_css_color(self):
        return "rgb{}".format(self.rgb)


def smart_hex(color_or_hex):
    if isinstance(color_or_hex, Color):
        return color_or_hex.hex
    else:
        return Color(hex=color_or_hex).hex


