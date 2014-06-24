import unittest

from jumpgate.common.utils import lookup
from jumpgate.common.utils import get_usable_ip


class TestLookup(unittest.TestCase):
    def test_lookup(self):
        self.assertEquals(lookup({}, 'key'), None)

        self.assertEquals(lookup({'key': 'value'}, 'key'), 'value')
        self.assertEquals(
            lookup({'key': {'key': 'value'}}, 'key', 'key'), 'value')

    def test_get_usable_ip(self):
        start_ip, end_ip = get_usable_ip('9.0.3.193', '9.0.3.192/29')
        self.assertEquals(start_ip, '9.0.3.194')
        self.assertEquals(end_ip, '9.0.3.198')

    def test_get_usable_ip_invalid_range(self):
        self.assertRaises(Exception, get_usable_ip,
                          '9.0.3.192', '9.0.3.192/29')

    def test_get_usable_ip_invalid_cidr(self):
        self.assertRaises(Exception, get_usable_ip, '9.0.3.192', '9.0.3.192')
