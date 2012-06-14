fahrplan.py
===========

.. image:: https://secure.travis-ci.org/gwrtheyrn/fahrplan.py.png?branch=master
    :alt: Build status
    :target: http://travis-ci.org/gwrtheyrn/fahrplan.py

Goal: Simple access to the sbb timetable service from the commandline with human
readable argument parsing.

Relies on the public transport API by opendata.ch: http://transport.opendata.ch/


Installing
----------

To install current development version using pip, issue::

    $ sudo pip install -e git://github.com/gwrtheyrn/fahrplan.py.git#egg=fahrplan-dev


Usage
-----

``fahrplan --help``::

    Usage:
     fahrplan [options] arguments

    Options:
     -v, --version Show version number
     -i, --info    Verbose output
     -d, --debug   Debug output
     -h, --help    Show this help

    Arguments:
     You can use natural language arguments using the following
     keywords in your desired language:
     en -- from, to, via, departure, arrival
     de -- von, nach, via, ab, an
     fr -- de, à, via, départ, arrivée

    Examples:
     fahrplan from thun to burgdorf
     fahrplan via bern nach basel von zürich, helvetiaplatz ab 15:35

.. image:: http://make.opendata.ch/lib/exe/fetch.php?media=project:20120331_160821.png
    :alt: Screenshot


Testing
-------

To run the tests, run the following command from the fahrplan module folder::

    $ python -m tests.test

If you have fabric installed, you can also use the `test` command::

    $ fab test


Sourcecode
----------

The sourcecode is available on Github: https://github.com/gwrtheyrn/fahrplan.py


License
-------

The code is licensed as GPLv3. See `LICENSE.md` for more details.