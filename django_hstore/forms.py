from __future__ import unicode_literals, absolute_import

try:
    import simplejson as json
except ImportError:
    import json

from django.forms import Field
import six
from django.utils.translation import ugettext
from django.core.exceptions import ValidationError

from .widgets import AdminHStoreWidget
from . import utils


def validate_hstore(value):
    """ HSTORE validation """
    # if empty
    if value == '' or value == 'null':
        value = '{}'

    # ensure valid JSON
    try:
        # convert strings to dictionaries
        if isinstance(value, six.string_types):
            dictionary = json.loads(value)
        # if not a string we'll check at the next control if it's a dict
        else:
            dictionary = value
    except ValueError as e:
        raise ValidationError(ugettext(u'Invalid JSON: {0}').format(e))

    # ensure is a dictionary
    if not isinstance(dictionary, dict):
        raise ValidationError(ugettext(u'No lists or values allowed, only dictionaries'))

    # convert any non string object into string
    for key, value in dictionary.items():
        if isinstance(value, dict) or isinstance(value, list):
            dictionary[key] = json.dumps(value)
        elif isinstance(value, bool) or isinstance(value, int) or isinstance(value, float):
            dictionary[key] = unicode(value).lower()

    return dictionary


class JsonMixin(object):

    def to_python(self, value):
        return validate_hstore(value)

    def render(self, name, value, attrs=None):
        # return json representation of a meaningful value
        # doesn't show anything for None, empty strings or empty dictionaries
        if value and not isinstance(value, six.string_types):
            value = json.dumps(value, sort_keys=True, indent=4)
        return super(JsonMixin, self).render(name, value, attrs)


class DictionaryFieldWidget(JsonMixin, AdminHStoreWidget):
    pass


class ReferencesFieldWidget(JsonMixin, AdminHStoreWidget):

    def render(self, name, value, attrs=None):
        value = utils.serialize_references(value)
        return super(ReferencesFieldWidget, self).render(name, value, attrs)


class DictionaryField(JsonMixin, Field):
    """
    A dictionary form field.
    """
    def __init__(self, **params):
        params['widget'] = params.get('widget', DictionaryFieldWidget)
        super(DictionaryField, self).__init__(**params)


class ReferencesField(JsonMixin, Field):
    """
    A references form field.
    """
    def __init__(self, **params):
        params['widget'] = params.get('widget', ReferencesFieldWidget)
        super(ReferencesField, self).__init__(**params)

    def to_python(self, value):
        value = super(ReferencesField, self).to_python(value)
        return utils.unserialize_references(value)
