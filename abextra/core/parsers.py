import datetime
import re

class price_parser():
    """Parses all numerics with left ctx of '$' and right ctx of 'dollar*'.
    Uses a very naive regex with one look-behind and one look-ahead.
    Numerics are of loose format.  Ex. 1, 2.2, 3.33, 4,444, 5,555,555.55
    """
    _PRICE_PATTERN = re.compile(
        r'(?P<lctx>[\$])?(?P<number>\d+(,\d+)*(\.\d{1,2})?)(?P<rctx>\s*(dollar|usd))?',
        re.I)

    @staticmethod
    def parse(raw_value):
        parsed_prices = list()
        groupings = price_parser._PRICE_PATTERN.findall(raw_value)
        for grouping in groupings:
            if grouping[0] or grouping[4]:
                numeric = float(grouping[1].replace(',', ''))
                parsed_prices.append(numeric)
        return parsed_prices

class datetime_parser():
    """Opportunistic datetime parser."""
    @staticmethod
    def parse(dt_string, formats):
        dt = None
        for format in formats:
            try:
                dt = datetime.datetime.strptime(dt_string, format)
            except ValueError:
                pass
            else:
                break
        if not dt:
            raise ValueError('Unparseable date format: %s' % dt_string)
        return dt
