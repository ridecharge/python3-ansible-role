import unittest
from unittest.mock import MagicMock
import logging
import dns


class DnsRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.hosted_zone = 'ASAFSDF1231231'
        self.instance_id = 'i-abc123'
        self.logger_name = 'name'
        self.ip = '1.1.1.1'
        self.record_sets = dns.build_record_sets(self.conn, self.hosted_zone)
        self.logger = dns.build_logger(self.logger_name, self.instance_id)
        self.logger.setLevel(logging.ERROR)
        self.registration = dns.DnsRegistration(self.record_sets,
                                                self.build_record(),
                                                self.ip,
                                                self.logger)

    def test_build_dns(self):
        self.assertEqual(self.build_record(), 'ntp-1a.ec2.gc')

    def build_record(self):
        az = 'us-east-1a'
        name = 'ntp'
        domain = 'ec2.gc'
        return dns.build_record(name, domain, az)

    def test_build_record_set(self):
        self.assertEqual(self.record_sets.hosted_zone_id, self.hosted_zone)

    def test_build_logger(self):
        self.assertEqual(self.logger.name, self.logger_name)
        self.assertIn(self.instance_id, self.logger.handlers[0].url)

    def test_dns_registration_init(self):
        self.assertEqual(self.record_sets, self.registration.record_sets)
        self.assertEqual(self.build_record(), self.registration.record)
        self.assertEqual(self.ip, self.registration.ip)
        self.assertEqual(self.logger, self.registration.logger)

    def test_split_domain(self):
        name, levels = dns.split_domain('ntp.ec2.gc')
        self.assertEqual(name, 'ntp')
        self.assertEqual(levels, 'ec2.gc')

    def test_dns_registration_register(self):
        change = MagicMock()
        record_sets = MagicMock()
        record_sets.add_change = MagicMock(return_value=change)
        self.registration.record_sets = record_sets
        self.registration.register()
        record_sets.add_change.assert_called_with('UPSERT', self.registration.record, 'A')
        change.add_value.assert_called_with(self.ip)
        record_sets.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
