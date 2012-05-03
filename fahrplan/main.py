#!/usr/bin/env python
# -*- coding: utf-8 -*-

# A SBB/CFF/FFS commandline based timetable client.
# Copyright (C) 2012 Danilo Bargen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
from datetime import date, time
import json
import requests
import dateutil.parser
import meta
from tableprinter import Tableprinter

API_URL = 'http://transport.opendata.ch/v1'


def main():

    """Parse arguments."""

    # Human parsing
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'von':

        keywords = ['von', 'nach', 'via', 'ab', 'an']
        keywords_required = ['von', 'nach']
        for keyword in keywords_required:
            assert keyword in sys.argv, '"%s" not provided.' % keyword

        class DictObj(object):
            def __init__(self, d):
                self.d = d
            def __getattr__(self, m):
                return self.d.get(m, None)

        data = {}
        current_kw = None
        for arg in sys.argv[1:]:
            if arg in keywords:
                current_kw = arg
                data[current_kw] = ''
            else:
                data[current_kw] = ('%s %s' % (data[current_kw], arg)).strip()

        args = DictObj({
            'start': data.get('von'),
            'destination': data.get('nach'),
            'via': data.get('via'),
            'departure': data.get('ab'),
            'arrival': data.get('an'),
        })

    # Argparse
    else:
        parser = argparse.ArgumentParser(
            prog=meta.title,
            description=meta.description,
            epilog='Disclaimer: This is not an official SBB app. The correctness \
                    of the data is not guaranteed.')
        parser.add_argument('start')
        parser.add_argument('destination')
        parser.add_argument('-v', '--via', help='set a via')
        parser.add_argument('-d', '--date', type=date, help='departure or arrival date')
        parser.add_argument('-t', '--time', type=time, help='departure or arrival time')
        parser.add_argument('-m', '--mode', choices=['dep', 'arr'], default='dep',
                help='time mode (date/time are departure or arrival)')
        parser.add_argument('--verbosity', type=int, choices=range(1, 4), default=2)
        parser.add_argument('--version', action='version', version='%(prog)s v' + meta.version)
        args = parser.parse_args()
        args.mode = 1 if args.mode == 'arr' else 0


    """Do API request."""

    url, params = build_request(args)
    try:
        response = requests.get(url, params=params)
    except requests.exceptions.ConnectionError:
        print 'Error: Could not reach network.'
        sys.exit(-1)
    try:
        data = json.loads(response.content)
    except ValueError:
        print 'Error: Invalid API response (invalid JSON)'
        sys.exit(-1)
    connections = data['connections']


    """Process data."""

    table = [parse_connection(c) for c in connections]

    # Define columns
    cols = (
        u'#', u'Station', u'Platform', u'Date', u'Time',
        u'Duration', u'Chg.', u'Travel with', u'Occupancy',
    )

    # Calculate and set column widths
    station_width = len(max([t['station_from'] for t in table] + \
                            [t['station_to'] for t in table],
                            key=len))
    travelwith_width = len(max([t['travelwith'] for t in table], key=len))
    widths = (
        2,
        max(station_width, len(cols[1])),  # station
        max(4,  len(cols[2])),   # platform (TODO width)
        max(13, len(cols[3])),   # date
        max(5,  len(cols[4])),   # time
        max(5,  len(cols[5])),   # duration
        max(2,  len(cols[6])),   # changes
        max(travelwith_width, len(cols[7])),   # means (TODO width)
        max(9,  len(cols[8])),  # occupancy
    )

    # Initialize table printer
    tableprinter = Tableprinter(widths, separator=' | ')

    # Print the header line
    tableprinter.print_line(cols)
    tableprinter.print_separator()

    # Print data
    for i, row in enumerate(table, start=1):
        duration = row['arrival'] - row['departure']
        cols_from = (
            str(i),
            row['station_from'],
            row['platform_from'],
            row['departure'].strftime('%a, %d.%m.%y'),
            row['departure'].strftime('%H:%M'),
            ':'.join(unicode(duration).split(':')[:2]),
            row['change_count'],
            row['travelwith'],
            (lambda: u'1: %s' % row['occupancy1st'] if row['occupancy1st'] else u'-')(),
        )
        tableprinter.print_line(cols_from)

        cols_to = (
            '',
            row['station_to'],
            row['platform_to'],
            row['arrival'].strftime('%a, %d.%m.%y'),
            row['arrival'].strftime('%H:%M'),
            '',
            '',
            '',
            (lambda: u'2: %s' % row['occupancy2nd'] if row['occupancy2nd'] else u'-')(),
        )
        tableprinter.print_line(cols_to)

        tableprinter.print_separator()


def build_request(args):
    url = '%s/connections' % API_URL
    params = {}
    params = {
        'from': args.start,
        'to': args.destination,
    }
    if hasattr(args, 'via'):
        params['time'] = args.via
    if hasattr(args, 'departure'):
        params['time'] = args.departure
    return url, params


def parse_connection(connection):
    """Process a connection object and return a dictionary with cleaned data."""

    con_from = connection['from']
    con_to = connection['to']
    con_sections = connection['sections']
    data = {}
    transport_means = lambda s: s['journey']['category'] if 'journey' in s else 'walk'
    categories = set(map(transport_means, con_sections))

    data['station_from'] = con_from['station']['name']
    data['station_to'] = con_to['station']['name']
    data['departure'] = dateutil.parser.parse(con_from['departure'])
    data['arrival'] = dateutil.parser.parse(con_to['arrival'])
    data['platform_from'] = con_from['platform']
    data['platform_to'] = con_to['platform']
    data['change_count'] = unicode(len(con_sections) - 1)
    data['travelwith'] = ', '.join(filter(None, categories))

    occupancies = {
        None: u'',
        '-1': u'',
        '0': u'Low',  # todo check
        '1': u'Low',
        '2': u'Medium',
        '3': u'High',
    }

    data['occupancy1st'] = occupancies.get(con_from['prognosis']['capacity1st'], u'')
    data['occupancy2nd'] = occupancies.get(con_from['prognosis']['capacity2nd'], u'')

    return data


if __name__ == '__main__':
    main()
