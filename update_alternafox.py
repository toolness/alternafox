import os
import sys
import HTMLParser
import re
import urllib2
import subprocess
import shutil
import time

index_urls = {
    'Aurora': "http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/latest-mozilla-aurora/",
    'Nightly': "http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/latest-trunk/"
}

class FtpIndexPageHtmlParser(HTMLParser.HTMLParser):
    file_re = re.compile(r'firefox-(.+)\.en-US\.mac\.dmg')

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.matches = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs = dict(attrs)
            if 'href' in attrs:
                match = self.file_re.match(attrs['href'])
                if match:
                    self.matches.append(dict(filename=match.group(0),
                                             version=match.group(1)))

    def get_latest_version(self):
        self.matches.sort(key=lambda x: x['version'],
                          cmp=compare_version)
        return self.matches[-1]

def find_latest_version_url(base_url, urlopen=urllib2.urlopen):
    index = urlopen(base_url)
    parser = FtpIndexPageHtmlParser()
    parser.feed(index.read())
    latest_version = parser.get_latest_version()
    return base_url + latest_version['filename']

CHUNK_SIZE = 1024 * 1024

def download_and_mount_dmg(fileobj, filename, volume_name):
    target = open(filename, 'wb')
    print "downloading (each dot is %dK)" % (CHUNK_SIZE / 1024),
    while True:
        chunk = fileobj.read(CHUNK_SIZE)
        if not chunk:
            break
        target.write(chunk)
        sys.stdout.write('.')
        sys.stdout.flush()
    print
    fileobj.close()
    target.close()
    print "mounting %s" % filename
    subprocess.check_call(['/usr/bin/hdid', filename])

def hack_application_ini(source_text, name):
    return source_text.replace('Name=Firefox', 'Name=%s' % name)

def unmount(volume_name):
    path = '/Volumes/%s' % volume_name
    print "unmounting %s" % path
    try:
        subprocess.check_call(['/sbin/umount', path])
    except Exception:
        print "something weird happened, forcing unmount."
        subprocess.check_call(['/usr/sbin/diskutil', 'unmount', 'force', path])

def get_app_dir(volume_name):
    return '/Applications/%s.app' % volume_name

def is_app_running(volume_name):
    app_dir = get_app_dir(volume_name)
    p = subprocess.Popen(['/bin/ps', '-ef'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    return (app_dir in out)

def download_and_install(fileobj, volume_name):
    dmg_name = '%s.dmg' % volume_name
    download_and_mount_dmg(fileobj, dmg_name, volume_name)

    src_dir = '/Volumes/%s/%s.app' % (volume_name, volume_name)
    app_dir = get_app_dir(volume_name)
    if os.path.exists(app_dir):
        print "deleting old app at %s" % app_dir
        shutil.rmtree(app_dir)
    print "copying from disk image at %s to %s" % (src_dir, app_dir)
    shutil.copytree(src_dir, app_dir)

    print "hacking application.ini"
    app_ini_filename = '%s/Contents/MacOS/application.ini' % app_dir
    old_app_ini = open(app_ini_filename, 'rb').read()
    new_app_ini = hack_application_ini(old_app_ini, volume_name)
    open(app_ini_filename, 'wb').write(new_app_ini)

    unmount(volume_name)
    print "deleting %s" % dmg_name
    os.unlink(dmg_name)
    
    print "Congratulations, you've got a new browser at %s." % app_dir

class VersionPart(object):
    '''
    Examples:

      >>> VersionPart('1')
      (1, None, 0, None)

      >>> VersionPart('1pre')
      (1, 'pre', 0, None)

      >>> VersionPart('1pre10')
      (1, 'pre', 10, None)

      >>> VersionPart('1pre10a')
      (1, 'pre', 10, 'a')

      >>> VersionPart('1+')
      (2, 'pre', 0, None)

      >>> VersionPart('*').numA == sys.maxint
      True

      >>> VersionPart('1') < VersionPart('2')
      True

      >>> VersionPart('2') > VersionPart('1')
      True

      >>> VersionPart('1') == VersionPart('1')
      True

      >>> VersionPart('1pre') > VersionPart('1')
      False

      >>> VersionPart('1') < VersionPart('1pre')
      False

      >>> VersionPart('1pre1') < VersionPart('1pre2')
      True

      >>> VersionPart('1pre10b') > VersionPart('1pre10a')
      True

      >>> VersionPart('1pre10b') == VersionPart('1pre10b')
      True

      >>> VersionPart('1pre10a') < VersionPart('1pre10b')
      True

      >>> VersionPart('1') > VersionPart('')
      True
    '''

    _int_part = re.compile('[+-]?(\d*)(.*)')
    _num_chars = '0123456789+-'

    def __init__(self, part):
        self.numA = 0
        self.strB = None
        self.numC = 0
        self.extraD = None

        if not part:
            return

        if part == '*':
            self.numA = sys.maxint
        else:
            match = self._int_part.match(part)
            self.numA = int(match.group(1))
            self.strB = match.group(2) or None
        if self.strB == '+':
            self.strB = 'pre'
            self.numA += 1
        elif self.strB:
            i = 0
            num_found = -1
            for char in self.strB:
                if char in self._num_chars:
                    num_found = i
                    break
                i += 1
            if num_found != -1:
                match = self._int_part.match(self.strB[num_found:])
                self.numC = int(match.group(1))
                self.extraD = match.group(2) or None
                self.strB = self.strB[:num_found]

    def _strcmp(self, str1, str2):
        # Any string is *before* no string.
        if str1 is None:
            if str2 is None:
                return 0
            else:
                return 1

        if str2 is None:
            return -1

        return cmp(str1, str2)

    def __cmp__(self, other):
        r = cmp(self.numA, other.numA)
        if r:
            return r

        r = self._strcmp(self.strB, other.strB)
        if r:
            return r

        r = cmp(self.numC, other.numC)
        if r:
            return r

        return self._strcmp(self.extraD, other.extraD)

    def __repr__(self):
        return repr((self.numA, self.strB, self.numC, self.extraD))

def compare_version(a, b):
    '''
    Examples:

      >>> compare_version('1', '2')
      -1

      >>> compare_version('1', '1')
      0

      >>> compare_version('2', '1')
      1

      >>> compare_version('1.0pre1', '1.0pre2')
      -1

      >>> compare_version('1.0pre2', '1.0')
      -1

      >>> compare_version('1.0', '1.0.0')
      0

      >>> compare_version('1.0.0', '1.0.0.0')
      0

      >>> compare_version('1.0.0.0', '1.1pre')
      -1

      >>> compare_version('1.1pre', '1.1pre0')
      0

      >>> compare_version('1.1pre0', '1.0+')
      0

      >>> compare_version('1.0+', '1.1pre1a')
      -1

      >>> compare_version('1.1pre1a', '1.1pre1')
      -1

      >>> compare_version('1.1pre1', '1.1pre10a')
      -1

      >>> compare_version('1.1pre10a', '1.1pre10')
      -1
    '''

    a_parts = a.split('.')
    b_parts = b.split('.')

    if len(a_parts) < len(b_parts):
        a_parts.extend([''] * (len(b_parts) - len(a_parts)))
    else:
        b_parts.extend([''] * (len(a_parts) - len(b_parts)))

    for a_part, b_part in zip(a_parts, b_parts):
        r = cmp(VersionPart(a_part), VersionPart(b_part))
        if r:
            return r

    return 0

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print "usage: %s [dmg-path] aurora|nightly"
        sys.exit(1)
    if len(sys.argv) == 2:
        dmg_path = None
        volume_name = sys.argv[1]
    elif len(sys.argv) == 3:
        dmg_path = os.path.expanduser(sys.argv[1])
        volume_name = sys.argv[2]
    volume_name = volume_name.capitalize()
    if volume_name not in index_urls:
        print "unknown alternafox: %s" % volume_name
        sys.exit(1)
    if is_app_running(volume_name):
        print "The %s browser is currently running." % volume_name
        print "Please close it first."
        sys.exit(1)
    if dmg_path:
        download = open(dmg_path, 'rb')
    else:
        print "finding latest version of %s" % volume_name
        url = find_latest_version_url(index_urls[volume_name])
        print "retrieving %s" % url
        download = urllib2.urlopen(url)
    download_and_install(download, volume_name)
    
if __name__ == '__main__':
    main()
