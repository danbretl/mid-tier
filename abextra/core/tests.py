from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase
from django.test.testcases import TransactionTestCase
from core.parsers import PriceParser

class PriceParserTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(PriceParserTest, cls).setUpClass()
        cls.parser = PriceParser()

    def test_multiple_prices_with_two_decimals_in_prose(self):
        price = '  Sign up by May 9th for a special discount. Early Registration 99.00 <br><br>  \
        Sign up for the Pedestrian Consulting Mailing list following purchase to receive a 10% discount \
        on the regular price course fee. See details below. Reduced Student Price -10% 250.00 <br><br>   \
        Regular Student PriceOLD 199.00 <br><br>  Attend a meetup to find out how to become a member. \
        Email info@pedestrianconsulting.com to find out how to become a member. Member Price 99.00 <br><br>   \
        Non-Member Price 125.00 <br><br>  This is a 2 hour group hands on session. \
        It is only available on Sept 5th Tuesday Sept 13th at 7 - 9 pm. \
        The August 24th date is for the 3 hour class Sept 13th Website Bootcamp Lab 52.24 <br><br>  \
        This is only held on Wednesday 8/24 at 7 - 9 pm. The other dates listed are for the labs \
        August 24th 3 hour Class 77.87 <br><br>   October 24th Class 77.87 <br><br>\n'
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual(
            (99.0, 250.0, 199.0, 99.0, 125.0, 7.0, 52.24, 7.0, 77.87, 77.87),
            tuple(parsed_prices), 'Unexpected prices value'
        )

    def test_single_price_with_two_decimals(self):
        price = '   RSVP 11.24 <br><br>\n'
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((11.24,), tuple(parsed_prices), 'Unexpected prices value')

    def test_single_price_with_commas_two_decimals_and_no_units(self):
        price = "   General Registration 2,395.00 <br><br>   Early Bird 2,195.00 <br><br>\n"
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((2395.0, 2195.0), tuple(parsed_prices), 'Unexpected prices value')

    def test_single_price_with_units_in_USD(self):
        price = "5 - 5 USD "
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((5.0, 5.0), tuple(parsed_prices), 'Unexpected prices value')

    def test_single_price_with_units_in_dollar_sign(self):
        price = "$35"
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((35.0,), tuple(parsed_prices), 'Unexpected prices value')

    def test_single_price_with_decimals_and_units_in_dollar_sign(self):
        price = "$10.00"
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((10.0,), tuple(parsed_prices), 'Unexpected prices value')

    def test_multiple_prices_with_some_units_and_some_decimals(self):
        price = "  35% off reg $300 Saturdays 4:30-5:45 pm, 10/1-11/19 195.00 <br><br>\n"
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((300.0, 195.0), tuple(parsed_prices), 'Unexpected prices value')

    def test_single_price_numeric_no_context(self):
        price = '75'
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((75,), tuple(parsed_prices))

    def test_two_prices_comma_separated(self):
        price = '1,2'
        parsed_prices = self.parser.parse(price)
        self.assertTupleEqual((1, 2), tuple(parsed_prices), 'Unexpected prices value')
