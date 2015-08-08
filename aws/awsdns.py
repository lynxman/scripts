#!/usr/bin/env python

from boto.route53.exception import DNSServerError
from boto import utils
import boto.ec2
import sys
import os
import argparse, ConfigParser

def dnsupdater(fqdn, ipaddr):
    """ This updates the DNS name providing fqdn and IP """
    from area53 import route53
    # A bit hacky, here I choose which domain I need to search, in this case I use subdomains
    domain = '.'.join(fqdn.split('.')[-3:])
    zone = route53.get_zone(domain)
    arec = zone.get_a(fqdn)

    if arec:
        old_value = arec.resource_records[0]
        if old_value == ipaddr:
            print '%s is current. (%s)' % (fqdn, ipaddr)
            return True

        print 'Updating %s: %s -> %s' % (fqdn, old_value, ipaddr)

        try:
            zone.update_a(fqdn, ipaddr, 900)

        except DNSServerError:
            # This can happen if the record did not already exist. Let's
            # try to add_a in case that's the case here.
            zone.add_a(fqdn, ipaddr, 900)
    else:
        print 'Adding %s:%s' % (fqdn, ipaddr)
        zone.add_a(fqdn, ipaddr, 900)

if __name__ == "__main__":
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="Location of the config file")
    args = parser.parse_args()

    # Read config file and parse
    if args.config:
        configfile = args.config
    else:
        configfile = "/etc/awsdns.conf"
    unparsed_config = ConfigParser.ConfigParser(allow_no_value=True)
    try:
        with open(configfile):
            unparsed_config.read(configfile)
            # pylint: disable=W0212
            config = unparsed_config._sections
    except IOError:
        print "Could not read config file %s, exiting\n" % configfile
        parser.print_help()
        sys.exit(1)

    # Populated from config
    env = config['dns']['env']
    nametag = config['dns']['nametag']
    private_domain = config['dns']['private_domain']
    public_domain = config['dns']['public_domain']
    os.environ["AWS_ACCESS_KEY_ID"] = config['aws']['aws_access_key']
    os.environ["AWS_SECRET_ACCESS_KEY"] = config['aws']['aws_secret_key']

    # Populate metadata
    metadata = utils.get_instance_metadata()

    hostname = metadata['local-hostname'].split('.')[0]
    localip = metadata['local-ipv4']
    publicip = metadata['public-ipv4']
    az = metadata['placement']['availability-zone']
    region = az[:-1]

    # Register tag values
    if nametag != "":
        dnsupdater("%s.%s.%s.%s" % (nametag, region, env, public_domain), publicip)
        dnsupdater("%s.%s.%s.%s" % (nametag, region, env, private_domain), localip)

    # Register host values
    dnsupdater("%s.%s.%s.%s" % (hostname, region, env, public_domain), publicip)
    dnsupdater("%s.%s.%s.%s" % (hostname, region, env, private_domain), localip)
