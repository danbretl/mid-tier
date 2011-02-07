#
# Author: Vikas Menon
# Date: 2/6/2011
#

import settings
import ml
import unittest


class MLModuleTest(unittest.TestCase):
    """
    This module tests the ML algorithm functions
    """

    def setUp(self):
        self.unitArray = [1] * 10
        self.emptyArray = []
        self.rangeArray = range(100)
        None

    def test_normalize(self):
        self.assertEqual(ml.normalize(unitArray), [1.0 / len(unitArray)] * len(unitArray))
        self.assertEqual(ml.normalize(emptyArray), [])
        self.assertEqual(ml.normalize(rangeArray), [(x * 2.0) / (len(unitArray) * (len(unitArray) - 1)) for x in rangeArray])

    def test_topN_function_generator(self):
        for k in [x + 1 for x in range(5)]:
            topkFunction = settings.topN_function(k)
            self.assertEqual(topkFunction(unitArray), 1.0)
            self.assertEqual(topkFunction(emptyArray), 0.0)
            self.assertEqual(topkFunction(rangeArray), settings.mean(rangeArray[-k:]))

if __name__ == '__main__':
    unittest.main()
