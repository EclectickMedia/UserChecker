import argparse
import sys
import time
from platform import system

import core
from core import ERR_FILE, OUT_FILE

l = core.Loader()


parser = argparse.ArgumentParser()
parser.add_argument('-q', '--quiet', help='Do not output to STDOUT',
                    action='store_true')

parser.add_argument('-r', '--iprange', help='The IP range to attempt to '
                    'scan. Defaults to \'192.168.1.0/24\'',
                    type=str, default='192.168.1.0/24')

parser.add_argument('-R', '--reset', help='Reset the on line status of the'
                    ' users in the database', action='store_true')

parsed = parser.parse_args()

if parsed.reset:
    core.reset(l.load())
    exit()

start_time = time.time()
while 1:
    # Clear OUT_FILE
    OUT_FILE.truncate(0)

    if not parsed.quiet:
        print('Refreshing DB')

    # Load a db
    db = l.load()

    if not parsed.quiet:
        print('Running NMAP to find connected devices.')

    # Generate an NMAP object, and wait for it to finish its scan
    core.generate_nmap(OUT_FILE, parsed.iprange).wait()

    for person in core.check_for_people(db, parsed.quiet):
        core.announce(person.name)

    if (time.time() - start_time) > 1200:  # TODO what is this doing here?
        ERR_FILE.truncate(0)
        start_time = time.time()

    l.dump(db)  # Dump db back to disk

    if not sys.argv.count('-q'):
        sys.stdout.truncate(0)