import unittest
import doctest

import update_alternafox
from update_alternafox import *

def get_sample_aurora_feed():
    p = FtpIndexPageHtmlParser()
    p.feed(open('sample_aurora_index.html', 'r').read())
    return p

class Tests(unittest.TestCase):
    def test_html_parser_feed(self):
        p = get_sample_aurora_feed()
        self.assertEqual(p.matches, [{'version': '5.0a2', 'filename': 'firefox-5.0a2.en-US.mac.dmg'}, {'version': '6.0a2', 'filename': 'firefox-6.0a2.en-US.mac.dmg'}])

    def test_html_parser_get_latest_version(self):
        p = get_sample_aurora_feed()
        self.assertEqual(p.get_latest_version()['version'], '6.0a2')

    def test_find_latest_version_url(self):
        def fake_urlopen(url):
            return open('sample_aurora_index.html', 'r')
        
        url = find_latest_version_url('http://foo.com/', fake_urlopen)
        self.assertEqual(url, 'http://foo.com/firefox-6.0a2.en-US.mac.dmg')

    def test_get_app_dir(self):
        self.assertEqual(get_app_dir('Foo'), '/Applications/Foo.app')

    def test_hack_application_ini(self):
        orig = '; hi\n\n[App]\nName=Firefox\n'
        expected = '; hi\n\n[App]\nName=Aurora\n'
        self.assertEqual(hack_application_ini(orig, 'Aurora'), expected)

if __name__ == '__main__':
    tests = []
    loader = unittest.TestLoader()
    module = __import__('__main__')
    suite = loader.loadTestsFromModule(module)
    for test in suite:
        tests.append(test)

    finder = doctest.DocTestFinder()
    doctests = finder.find(update_alternafox)
    for test in doctests:
        if len(test.examples) > 0:
            tests.append(doctest.DocTestCase(test))

    suite = unittest.TestSuite(tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
