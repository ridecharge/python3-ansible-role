#!/usr/bin/env python3
import boto.utils
import boto.route53
import logging
import loggly.handlers
import sys


class DnsRegistration(object):
    def __init__(self, record_sets, record, ip, logger):
        self.record_sets = record_sets
        self.record = record
        self.ip = ip
        self.logger = logger
        self.logger.info("DnsRegistration init with {0.record_sets.hosted_zone_id} {0.ip}.".format(self))


    def register(self):
        """ Upserts the A record """
        change = self.record_sets.add_change('UPSERT', self.record, 'A')
        change.add_value(self.ip)
        self.record_sets.commit()
        self.logger.info("Successful set {0.ip} to {0.record}.".format(self))


def build_record(name, domain, az):
    """ Rebuilds the DNS record with postfix of the zone.
    ntp.example.com at us-east-1a becomes ntp-1a.example.com
    for paramters
    name=ntp 
    domain=example.com  
    az=us-east-1a 
    """
    zone = az.split('-')[-1]
    return "{}-{}.{}".format(name, zone, domain)


LOGGLY_URL = "https://logs-01.loggly.com/inputs/"+ \
             "e8bcd155-264b-4ec0-88be-fcb023f76a89/tag/python,boot,dns,cloudformation"


def build_logger(name, instance_id):
    """ Sets up a logger to send files to Loggly with dynamic tags """
    logger = logging.getLogger(name)
    url = ",".join([LOGGLY_URL, instance_id])
    print(url)
    handler = loggly.handlers.HTTPSHandler(url)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def build_record_sets(conn, hosted_zone):
    """ Returns a Route53 RecordSets for the hosted_zone and connection """
    return boto.route53.record.ResourceRecordSets(conn, hosted_zone)


def split_domain(domain):
    """ Splits the domain into the first part and then the rest as a tuple """
    levels = domain.split('.', 1)
    name = levels[0]
    return name, levels[1]


def main(hosted_zone, domain):
    name, levels = split_domain(domain)
    instance_metadata = boto.utils.get_instance_metadata()
    logger = build_logger(name, instance_metadata['instance-id'])

    try:
        region = boto.utils.get_instance_identity()['document']['region']
        az = instance_metadata['placement']['availability-zone']
        conn = boto.route53.connect_to_region(region)

        DnsRegistration(build_record_sets(conn, hosted_zone),
                        build_record(name, levels, az),
                        instance_metadata['local-ipv4'],
                        logger
        ).register()
    except:
        logger.exception('Error Registering DNS')

# Takes a Route53 Hosted Zone as the first parameters.
# Takes a domain name in the form ntp.example.com as the second parameter.
# Called on startup for 
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
