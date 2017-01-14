#! /Library/Frameworks/Python.framework/Versions/3.5/bin/python3
import subprocess
from os import system
import pickle
import time
import sys
import signal
import argparse
from tempfile import NamedTemporaryFile

ERR_FILE = NamedTemporaryFile('a+')
OUT_FILE = NamedTemporaryFile('a+')
DB_PATH = 'db.pkl'


def load_db(path='db.pkl'):
    """ Loads a dict object containing the following fields:

        name - The name of the maker
        ident - The unique network identifier.
        is_connected - True if user is on the wifi, false otherwise.
    """
    with open(path, 'rb') as f:
        return pickle.load(f)


def dump_db(db, path='db.pkl'):
    with open(path, 'wb+') as f:
        pickle.dump(db, f)


def generate_nmap(output_file, ip_range='192.168.1.0/24'):
    return subprocess.Popen(['nmap', '-sP', ip_range], stdout=output_file,
                            stderr=ERR_FILE)


def grep_output(term, output_file):
    if not sys.argv.count('-q'):
        print('....Searching for %s' % term)
    for line in output_file:
        if line.count(term):
            return True

    else:
        return False


def say_hello(output='Tee is home!'):
    return subprocess.Popen(['say', output]).wait()


def reset(*args):
    db = load_db()
    for person in db:
        person['is_home'] = False
    dump_db(db)

    ERR_FILE.truncate(0)
    OUT_FILE.truncate(0)

    if not sys.argv.count('-q'):
        print('Exiting!')
    sys.exit(0)


def check_for_people(db, quiet):
    for person in db:

        if not quiet:
            print('Grepping output for %s using the search term %s.'
                  % (person['name'], person['ident']))

        with open('outlog.txt') as f:
            if grep_output(person['ident'], f):

                if not person['is_connected']:
                    if not quiet:
                        print('%s connected to the WiFi!'
                              % person['name'])
                    person['is_connected'] = True
                    say_hello('%s connected to the WiFi!'
                              % person['name'])

            else:

                if person['is_connected']:

                    if not quiet:
                        print('%s disconnected from the WiFi!'
                              % person['name'])
                    say_hello('%s disconnected from the WiFi!'
                              % person['name'])

                person['is_connected'] = False


def run(quiet, iprange):
    start_time = time.time()
    while 1:
        OUT_FILE.truncate(0)

        if not quiet:
            print('Refreshing DB')

        db = load_db()

        if not quiet:
            print('Running NMAP to find connected devices.')

        if iprange is None:
            generate_nmap(OUT_FILE).wait()
        else:
            generate_nmap(OUT_FILE, ip_range=iprange).wait()

        check_for_people(db, quiet)

        if (time.time() - start_time) > 1200:
            ERR_FILE.truncate(0)
            start_time = time.time()

        # time.sleep(10)
        dump_db(db)

        if not sys.argv.count('-q'):
            system('clear')


signal.signal(signal.SIGINT, reset)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', help='Do not output to STDOUT',
                        action='store_true')

    parser.add_argument('-r', '--iprange', help='The IP range to attempt to '
                        'scan.', type=str)

    parsed = parser.parse_args()

    run(quiet=parsed.quiet, iprange=parsed.iprange)
