#!/usr/bin/env python

import gevent
import argparse
from gevent import monkey; monkey.patch_all()
import db
import util
import scan

from configurations import CONFIGURATIONS

site_table = []
header_name_table = {}
header_value_table = {}
header_table = []
headers_counter = {'name': 0, 'value': 0}

class Headers:

    def __init__(self):
        global settings, config, scanner
        config = util.Util()
        settings = config.load_config(CONFIGURATIONS)
        scanner = scan.Scan(settings)
        self.load_header_name_table()

    def load_header_name_table(self):
        global header_name_table
        for header_name in settings['headers']:
            self.test_duplicate_value(
                header_name,
                header_name_table,
                'name')

    def work_headers(self, item):
        global site_table, header_value_table, header_table
        site_id = item[0]
        site = item[1]
        url, code, headers = scanner.get_data(site)
        site_table.append([site_id, site, url, code])
        if code > 0:
            for header_name, header_value in headers:
                if header_name in header_name_table:
                    hvalue = self.test_duplicate_value(
                        header_value,
                        header_value_table,
                        'value')
                    header_table.append(
                        [site_id,
                        header_name_table[header_name],
                        hvalue])

    def test_duplicate_value(self, value, table, index_name):
        global headers_counter
        if value not in table:
            headers_counter[index_name] += 1
            table[value] = headers_counter[index_name]
            return headers_counter[index_name]
        else:
            return table[value]

    def save_data(self):
        database = db.DB(settings)
        database.populate_mysql(site_table, header_name_table, header_value_table, header_table)


    def main(self):
        parser = argparse.ArgumentParser(
            description='Headers will get all response headers from Alexa top sites.'
        )
        parser.add_argument(
            '-f',
            '--filename',
            default=settings['general']['topsites_filename'],
            help='Filename with list of sites.'
        )
        parser.add_argument(
            '-t',
            '--threads',
            type=int,
            default=settings['general']['thread_number'],
            help='Number of threads to make parallel request.'
        )
        args = parser.parse_args()

        filename = args.filename
        num_threads = args.threads
        dictsites = config.get_dictsites(filename)
        sites = len(dictsites)
        start = 0
        thread = 1
        while (start < sites):
            print('Thread pool {} ({} - {})'.format(thread, start, start + num_threads))
            thread += 1
            threads = [gevent.spawn(self.work_headers, item) for item in dictsites[start:start+num_threads]]
            gevent.joinall(threads)
            start += num_threads
        scanner.get_summary(site_table)
        self.save_data()
