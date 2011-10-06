import re

class BaseParser(object):
    """abstract base parser"""
    def parse(self, raw_value):
        raise NotImplementedError

class PriceParser(BaseParser):
    """Parses all numerics with left ctx of '$' and right ctx of 'dollar*'.
    Uses a very naive regex with one look-behind and one look-ahead.
    Numerics are of loose format.  Ex. 1, 2.2, 3.33, 4,444, 5,555,555.55
    """

    def __init__(self):
        self.rg = re.compile(
            r'(?P<lctx>[\$])?(?P<number>\d+(,\d+)*(\.\d{1,2})?)(?P<rctx>\s*dollar)?'
        )

    def parse(self, raw_value):
        parsed_prices = list()
        groupings = self.rg.findall(raw_value)
        for grouping in groupings:
            if grouping[0] or grouping[4]:
                numeric = float(grouping[1].replace(',', ''))
                parsed_prices.append(numeric)
        return parsed_prices

