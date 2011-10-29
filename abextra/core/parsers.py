import datetime
import re
from core.utils import html_sanitize

class price_parser():
    """Parses all numerics with left ctx of '$' and right ctx of 'dollar*'.
    Uses a very naive regex with one look-behind and one look-ahead.
    Numerics are of loose format.  Ex. 1, 2.2, 3.33, 4,444, 5,555,555.55
    """
    _PRICE_PATTERN = re.compile(
        r'(?P<lctx>[\$]|(coupon|redeem))?(?P<lws>\s+)?(?P<number>\d+(,\d+)*(\.\d{1,2})?)(?P<rws>\s+)?(?P<rctx>([\$]|dollar|usd|hours|am|pm))?',
        re.I)

    @staticmethod
    def parse(raw_value, non_contextualized=False):
        parsed_prices = list()
        sanitized_value = html_sanitize(raw_value)
        groupings = price_parser._PRICE_PATTERN.findall(sanitized_value.lower())
        for grouping in groupings:
            do_parse_grouping = False
            if grouping[0] or grouping[7]:
                do_parse_grouping = ('$' in grouping[0] or '$' in grouping[7] or 'dollars' in
                        grouping[7] or 'usd' in grouping[7])
            elif grouping[5]:
                do_parse_grouping = not ('coupon' in grouping[0] or 'redeem' in grouping[0]
                    or 'hours' in grouping[7] or 'am' in grouping[7] or
                            'pm' in grouping[7])
            if do_parse_grouping:
                numeric = float(grouping[3].replace(',', ''))
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
