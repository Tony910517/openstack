import unittest

class _Base(unittest.TestCase):

    def failUnless(self, predicate, message=''):
        self.assertTrue(predicate, message) # Nannies go home!

    def failIf(self, predicate, message=''):
        self.assertFalse(predicate, message) # Nannies go home!

class TestDefaultRequestClassifier(_Base):

    def _getFUT(self):
        from repoze.who.classifiers import default_request_classifier
        return default_request_classifier

    def _makeEnviron(self, kw=None):
        from wsgiref.util import setup_testing_defaults
        environ = {}
        setup_testing_defaults(environ)
        if kw is not None:
            environ.update(kw)
        return environ

    def test_conforms_to_IRequestClassifier(self):
        from repoze.who.interfaces import IRequestClassifier
        self.failUnless(IRequestClassifier.providedBy(self._getFUT()))

    def test_classify_dav_method(self):
        classifier = self._getFUT()
        environ = self._makeEnviron({'REQUEST_METHOD':'COPY'})
        result = classifier(environ)
        self.assertEqual(result, 'dav')

    def test_classify_dav_useragent(self):
        classifier = self._getFUT()
        environ = self._makeEnviron({'HTTP_USER_AGENT':'WebDrive'})
        result = classifier(environ)
        self.assertEqual(result, 'dav')

    def test_classify_xmlpost(self):
        classifier = self._getFUT()
        environ = self._makeEnviron({'CONTENT_TYPE':'text/xml',
                                     'REQUEST_METHOD':'POST'})
        result = classifier(environ)
        self.assertEqual(result, 'xmlpost')

    def test_classify_xmlpost_uppercase(self):
        """RFC 2045, Sec. 5.1: The type, subtype, and parameter names
           are not case sensitive"""
        classifier = self._getFUT()
        environ = self._makeEnviron({'CONTENT_TYPE':'TEXT/XML',
                                     'REQUEST_METHOD':'POST'})
        result = classifier(environ)
        self.assertEqual(result, 'xmlpost')

    def test_classify_rich_xmlpost(self):
        """RFC 2046, sec. 4.1.2: A critical parameter that may be specified
           in the Content-Type field for "text/plain" data is the character set.""" 
        classifier = self._getFUT()
        environ = self._makeEnviron({'CONTENT_TYPE':'text/xml; charset=UTF-8 (some comment)',
                                     'REQUEST_METHOD':'POST'})
        result = classifier(environ)
        self.assertEqual(result, 'xmlpost')

    def test_classify_browser(self):
        classifier = self._getFUT()
        environ = self._makeEnviron({'CONTENT_TYPE':'text/xml',
                                     'REQUEST_METHOD':'GET'})
        result = classifier(environ)
        self.assertEqual(result, 'browser')


class TestDefaultChallengeDecider(_Base):

    def _getFUT(self):
        from repoze.who.classifiers import default_challenge_decider
        return default_challenge_decider

    def _makeEnviron(self, kw=None):
        environ = {}
        environ['wsgi.version'] = (1,0)
        if kw is not None:
            environ.update(kw)
        return environ

    def test_conforms_to_IChallengeDecider(self):
        from repoze.who.interfaces import IChallengeDecider
        self.failUnless(IChallengeDecider.providedBy(self._getFUT()))

    def test_challenges_on_401(self):
        decider = self._getFUT()
        self.failUnless(decider({}, '401 Unauthorized', []))

    def test_doesnt_challenges_on_non_401(self):
        decider = self._getFUT()
        self.failIf(decider({}, '200 Ok', []))

class TestPassthroughChallengeDecider(_Base):

    def _getFUT(self):
        from repoze.who.classifiers import passthrough_challenge_decider
        return passthrough_challenge_decider

    def _makeEnviron(self, kw=None):
        environ = {}
        environ['wsgi.version'] = (1,0)
        if kw is not None:
            environ.update(kw)
        return environ

    def test_conforms_to_IChallengeDecider(self):
        from repoze.who.interfaces import IChallengeDecider
        self.failUnless(IChallengeDecider.providedBy(self._getFUT()))

    def test_challenges_on_bare_401(self):
        decider = self._getFUT()
        self.failUnless(decider({}, '401 Unauthorized', []))

    def test_doesnt_challenges_on_non_401(self):
        decider = self._getFUT()
        self.failIf(decider({}, '200 Ok', []))

    def test_doesnt_challenges_on_401_with_WWW_Authenticate(self):
        decider = self._getFUT()
        self.failIf(decider({}, '401 Ok', [('WWW-Authenticate', 'xxx')]))

    def test_doesnt_challenges_on_401_with_text_html(self):
        decider = self._getFUT()
        self.failIf(decider({}, '401 Ok', [('Content-Type', 'text/html')]))