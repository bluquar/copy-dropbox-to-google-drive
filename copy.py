# !/usr/bin/python
import curses
import filecmp
import locale
import os
import shutil
import sys
import time

SOURCE = '/Users/cbarker/Dropbox (Personal)'
DEST = '/Volumes/GoogleDrive/My Drive/Dropbox'

# If either the directory or filename contains any of these strings, it will be skipped
EXCLUDE_ANY = {
    '.dropbox',
    '.DS_Store',
    '.gdoc',
    '.gdraw',
    '.gform',
    '.git',
    '.glink',
    '.gmap',
    '.gsheet',
    '.gslides',
    'Music/iTunes/Album Artwork',
    'My Mac (cbarker-mbp)',
    'My Mac (cbarker-pro)',
}

# If the filename matches any of these exactly, it will be skipped
EXCLUDE_FILE = {
    'Icon',
    'Passwords app.dbx-passwords',
    'Vault.dbx-vault',
}

LAST_REFRESH_TIME = -1
stdscr = None
locale.setlocale(locale.LC_ALL, 'en_US')

def status_counter():
    """Create functions for tracking and summarizing the number of files that have various statuses"""
    COUNTS = {}

    def inc(key):
        """Increment the count for a particular status/outcome"""
        COUNTS[key] = 1 if key not in COUNTS else COUNTS[key] + 1

    def count_summary():
        """Get printable of statuses/outcomes"""
        ret = []
        max_key_len = 0 if len(COUNTS) == 0 else max(len(k) for k in COUNTS.iterkeys())
        count_fmt = '%%%ds: %%s' % max_key_len
        for i, t in enumerate(COUNTS.iteritems()):
            key, number = t
            number = locale.format("%d", number, grouping=True)
            ret.append(count_fmt % (key, number))
        return ret

    return inc, count_summary
inc, count_summary = status_counter()

PRINT_REFRESH_RATE_MS = 200
def report(checking):
    """Report the script's operation status to the terminal"""
    # Only update the terminal at most once every PRINT_REFRESH_RATE_MS ms
    global LAST_REFRESH_TIME
    global stdscr
    now = int(round(time.time() * 1000))
    if (now - LAST_REFRESH_TIME) < PRINT_REFRESH_RATE_MS:
        return
    LAST_REFRESH_TIME = now

    stdscr.clear()
    for i, summary in enumerate(count_summary()):
        stdscr.addstr(i, 0, summary)
    stdscr.addstr(i + 2, 0, 'Checking: %s' % checking)
    stdscr.refresh()

def are_files_equal(f1, f2):
    # This is a very expensive way of comparing, so I'm commenting it out for now
    # with open(dest_absolute) as dest_file:
    #     dest_contents = dest_file.read()
    # with open(source_absolute) as source_file:
    #     source_contents = source_file.read()
    size_1 = os.path.getsize(f1)
    size_2 = os.path.getsize(f2)
    return size_1 == size_2

def process(dir, filename):
    """Process one file"""

    # dir is like "Documents/Financial"
    # filename is like "Statement.pdf"

    # joined is like "Documents/Financial/Statement.pdf"
    joined = os.path.join(dir, filename)

    # dest_dir is like "GoogleDrive/Documents/Financial"
    dest_dir = os.path.join(DEST, dir)

    # source_absolute is like "Dropbox/Documents/Financial/Statement.pdf"
    source_absolute = os.path.join(SOURCE, joined)

    # dest_absolute is like "GoogleDrive/Documents/Financial/Statement.pdf"
    dest_absolute = os.path.join(DEST, joined)

    if (os.path.exists(dest_absolute)):
        # There is already a file there. Let's check if it has the correct contents
        are_equal = are_files_equal(source_absolute, dest_absolute)
        if are_equal:
            inc('Already Exists & Equal')
            # If it already has the right contents, then we're done and can return early
            return
        else:
            # If it doesn't have the right contents, add it to a list of files that
            # have the wrong contents so the user can audit this
            with open('unequal.txt', 'a') as f:
                f.write(joined + '\n')

            inc('Already Exists but NOT Equal')

            # And don't return, so that we can continue to the copying code
    try:
        # Try creating any directories that we need to in order to start copying the file
        try:
            os.makedirs(dest_dir)
        except Exception as ee:
            # Ignore the exception if it's complaining that the directories are already there
            if 'File exists:' not in str(ee):
                raise ee

        # Try copying the file from the source location to the destination location
        shutil.copy2(source_absolute, dest_dir)

        # If we successfully copied a file, add it to a list of files
        # that were successfully copied so the user can audit this
        with open('copied.txt', 'a') as f:
            f.write(joined + '\n')
        return inc('Successfully copied')
    except Exception as e:
        # If there was an exception when we were trying to copy the file, add
        # it to a list of files that had failures so that the user can audit this
        with open('failures.txt', 'a') as f:
            f.write(joined + '\n')
            # Also record what the exception was
            f.write('  ' + str(e) + '\n')
        return inc('Failed to copy')

def check(dir, filename):
    """Filter out irrelevant files and dispatch to `process` and `report` helper functions"""
    if (filename.strip() in EXCLUDE_FILE):
        return
    dir = dir[len(SOURCE) + 1:]
    if any(e in dir or e in filename for e in EXCLUDE_ANY):
        return
    joined = os.path.join(dir, filename)

    process(dir, filename)
    report(joined)

def init_terminal():
    global stdscr
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()

def close_terminal():
    curses.echo()
    curses.nocbreak()
    curses.endwin()

def main():
    init_terminal()
    try:
        for root, _, files in os.walk(SOURCE):
            for name in files:
                check(root, name)
    finally:
        close_terminal()
        for summary in count_summary():
            print summary

if __name__ == '__main__':
    main()
