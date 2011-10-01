from dateutil import parser, rrule

class BaseArgConverter(object):

    def convert_value(self, value):
        """convert either a single value or sequence"""
        sequence = value.split(',')
        if len(sequence) > 1:
            return map(self._convert_value, sequence)
        return self._convert_value(value)

class ConstantArgConverter(BaseArgConverter):
    kwargs = ('freq', 'wkst', 'byweekday')

    def _convert_value(self, value):
        return getattr(rrule, value.upper())

class BooleanArgConverter(BaseArgConverter):
    kwargs = ('cache')

    def _convert_value(self, value):
        return bool(value)

class DateTimeArgConverter(BaseArgConverter):
    kwargs = ( 'dtstart', 'until' )

    def _convert_value(self, value):
        return parser.parse(value)

class IntegerArgConverter(BaseArgConverter):
    kwargs = ('bysetpos', 'bymonth', 'bymonthday', 'byyearday',
        'byweekno', 'byhour', 'byminute', 'bysecond', 'byeaster',
        'count', 'interval')

    def _convert_value(self, value):
        return int(value)

class ArgConverter(object):
    registry = (
        ConstantArgConverter, BooleanArgConverter,
        DateTimeArgConverter, IntegerArgConverter,
    )

    def __init__(self):
        self.arg_to_converter = dict()
        for converter_class in self.registry:
            converter = converter_class()
            for kwarg in converter.kwargs:
                self.arg_to_converter[kwarg.lower()] = converter

    def convert(self, kwarg, value):
        converter = self.arg_to_converter[kwarg.lower()]
        return converter.convert_value(value)

class RRuleConverter(object):
    arg_converter = ArgConverter()
    alias_mapping = {'byday':'byweekday'}

    def _convert(self, raw_rrule):
        args_raw = raw_rrule.split(';')
        rrule_kwargs = dict()
        for arg_raw in args_raw:
            kwarg, value = arg_raw.split('=')
            kwarg = self.alias_mapping.get(kwarg.lower(), kwarg)
            type_safe_value = self.arg_converter.convert(kwarg, value)
            rrule_kwargs[kwarg.lower()] = type_safe_value

        return rrule.rrule(**rrule_kwargs)

    def convert(self, raw_rrules):
        if isinstance(raw_rrules, (list,tuple)) and len(raw_rrules) > 1:
            return map(self._convert, raw_rrules)
        return self._convert(raw_rrules)
