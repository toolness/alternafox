import os
import HTMLParser
import re
import urllib2
import subprocess

import version_comparator

AURORA_INDEX_URL = "http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/latest-mozilla-aurora/"

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
                          cmp=version_comparator.compare)
        return self.matches[-1]

def find_latest_version_url(base_url, urlopen=urllib2.urlopen):
    index = urlopen(base_url)
    parser = FtpIndexPageHtmlParser()
    parser.feed(index.read())
    latest_version = parser.get_latest_version()
    return base_url + latest_version['filename']

CHUNK_SIZE = 1024 * 512

def download_and_mount_dmg(fileobj, filename, volume_name):
    target = open(filename, 'wb')
    while True:
        chunk = fileobj.read(CHUNK_SIZE)
        if not chunk:
            break
        target.write(chunk)
    fileobj.close()
    target.close()
    subprocess.check_call(['/usr/bin/hdid', filename])

def unmount(volume_name):
    subprocess.check_call(['/sbin/umount', '/Volumes/%s' % volume_name])

def download_and_install(fileobj, volume_name):
    dmg_name = '%s.dmg' % volume_name
    download_and_mount_dmg(fileobj, dmg_name, volume_name)
    # TODO: Install it!
    unmount(volume_name)
    os.unlink(dmg_name)
    
if __name__ == '__main__':
    download_and_install(open('/Users/atul/Downloads/firefox-5.0a2.en-US.mac.dmg', 'rb'), 'Aurora')
