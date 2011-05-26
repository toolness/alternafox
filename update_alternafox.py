import os
import sys
import HTMLParser
import re
import urllib2
import subprocess
import shutil
import time

import version_comparator

index_urls = {
    'Aurora': "http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/latest-mozilla-aurora/",
    'Nightly': "TODO"
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
                          cmp=version_comparator.compare)
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

def download_and_install(fileobj, volume_name):
    dmg_name = '%s.dmg' % volume_name
    download_and_mount_dmg(fileobj, dmg_name, volume_name)

    src_dir = '/Volumes/%s/%s.app' % (volume_name, volume_name)
    app_dir = '/Applications/%s.app' % volume_name
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

if __name__ == '__main__':
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
    if dmg_path:
        download = open(dmg_path, 'rb')
    else:
        print "finding latest version of %s" % volume_name
        url = find_latest_version_url(index_urls[volume_name])
        print "retrieving %s" % url
        download = urllib2.urlopen(url)
    download_and_install(download, volume_name)
