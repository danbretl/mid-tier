import datetime
import re
from lepl.matchers.combine import Or, And
from lepl.matchers.core import Any
from lepl.matchers.derived import UnsignedInteger, UnsignedReal, AnyBut, Join
from lepl.matchers.derived import Star, Drop, Whitespace, Optional, Digit, Add
from BeautifulSoup import BeautifulSoup

class PriceParser(object):
    punctuation = '!"#&\'()*+,.;<=>?@[\\]^_`{|}~'
    lctx_1_exceptions = set('/ :'.split())
    lctx_2_exceptions = set('discount redeem voucher'.split())
    rctx_1_exceptions = set('/ : th am pm hour hours %'.split())
    rctx_2_exceptions = set('discount redeem voucher'.split())

    def __init__(self, clean_html=True):
        self.clean_html = clean_html
        # lepl
        _comma_three_digits = Join(Drop(','), Add(Digit()[3]))[:]
        _thousand_group = Or(
            Join(_comma_three_digits, Any('.'), UnsignedInteger()),
            Join(_comma_three_digits, Optional(Any('.')))
        )
        _real = Or(Join(UnsignedInteger(), _thousand_group), UnsignedReal()) >> float
        _any = Join(Star(AnyBut(_real)))
        self.real_partition = Star(And(_any, _real, _any))
        self.real_simple = _real[:, Drop(Star(Or(Whitespace(), Any(',-'))))]

    def _clean_html(self, s):
        return ''.join(BeautifulSoup(s).findAll(text=True))

    def _condition_raw_string(self, s):
        if self.clean_html:
            s = self._clean_html(s)
        return s.strip().lower()

    def _optimizations(self, s):
        if len(s) < 1 or not re.search(r'\d+', s):
            return []
        try:
            return [float(s)]
        except Exception:
            try:
                return self.real_simple.parse(s)
            except Exception:
                return None

    def _ctx_list(self, s):
        s = self._condition_raw_string(s)
        real_partitions = self.real_partition.parse(s)
        for i, e in enumerate(real_partitions):
            if isinstance(e, basestring):
                e = e.strip()
                ctx_elements = re.split(r'\s+', e)
                for j, ctx_e in enumerate(ctx_elements):
                    ctx_e = ctx_e.strip(self.punctuation)
                    if len(ctx_e) > 1 and not ctx_e.isalnum():
                        del ctx_elements[j]
                        ctx_elements.extend(list(ctx_e))
                    else:
                        ctx_elements[j] = ctx_e
                real_partitions[i] = ctx_elements
        return real_partitions

    def _ctx_reals(self, s):
        ret = []
        ctx_list = self._ctx_list(s)
        for i, e in enumerate(ctx_list):
            if isinstance(e, float):
                lctx = ctx_list[i - 1][-2:] if i > 0 and isinstance(ctx_list[i - 1], list) else None
                rctx = ctx_list[i + 1][:2] if i + 1 < len(ctx_list) and isinstance(ctx_list[i + 1], list) else None
                ret.append([lctx, e, rctx])
        return ret

    def parse(self, s):
        # optimizations
        res = self._optimizations(s)
        if res is not None:
            return res

        # contextualized analysis
        ret = []
        ctx_reals = self._ctx_reals(s)
        for lctx, real, rctx in ctx_reals:
            if lctx:
                if lctx[-1] in self.lctx_1_exceptions | self.lctx_2_exceptions: continue
                if len(lctx) > 1 and lctx[-2] in self.lctx_2_exceptions: continue
            if rctx:
                if rctx[0] in self.rctx_1_exceptions | self.rctx_2_exceptions: continue
                if len(rctx) > 1 and rctx[1] in self.rctx_2_exceptions: continue
            ret.append(real)
        return ret


#class price_parser():
#    """Parses all numerics with left ctx of '$' and right ctx of 'dollar*'.
#    Uses a very naive regex with one look-behind and one look-ahead.
#    Numerics are of loose format.  Ex. 1, 2.2, 3.33, 4,444, 5,555,555.55
#    """
#    _PRICE_PATTERN = re.compile(
#        r'(?P<lctx>[\$]|(coupon|redeem))?(?P<lws>\s+)?(?P<number>\d+(,\d+)*(\.\d{1,2})?)(?P<rws>\s+)?(?P<rctx>([\$]|dollar|usd|hours|am|pm))?',
#        re.I)
#
#    @staticmethod
#    def parse(raw_value):
#        parsed_prices = list()
#        sanitized_value = html_sanitize(raw_value)
#        try:
#            parsed_prices.append(float(raw_value))
#        except Exception:
#            groupings = price_parser._PRICE_PATTERN.findall(sanitized_value.lower())
#            for grouping in groupings:
#                do_parse_grouping = False
#                if grouping[0] or grouping[7]:
#                    do_parse_grouping = any(
#                        ('$' in grouping[0], '$' in grouping[7], 'dollars' in grouping[7], 'usd' in grouping[7])
#                    )
#                elif grouping[5]:
#                    do_parse_grouping = not any(
#                        ('coupon' in grouping[0], 'redeem' in grouping[0],
#                         'hours' in grouping[7], 'am' in grouping[7], 'pm' in grouping[7])
#                    )
#                if do_parse_grouping:
#                    numeric = float(grouping[3].replace(',', ''))
#                    parsed_prices.append(numeric)
#        return parsed_prices

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
