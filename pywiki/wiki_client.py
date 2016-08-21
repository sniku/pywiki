import datetime
import os
import os.path
import sys
import cmd
import configparser
import tempfile
from subprocess import call
from urllib.parse import urljoin

import furl
import html2text as html2text
import requests

CONFIG_FILE = os.path.expanduser('~/.config/wiki_client.conf')


class MediaWikiEditor(object):
    def open_article(self, initial_content, title=""):
        if title:  # sanitize for security
            title = "".join(x for x in title if x.isalnum())
        prefix = (title or "tmp") + "__["

        with tempfile.NamedTemporaryFile(prefix=prefix, suffix="].tmp.wiki", delete=False,) as tmpfile:
            tmpfile.write(initial_content.encode('utf8'))
            tmpfile.flush()
            editor_with_args = settings['editor'].split(" ") + [tmpfile.name]
            # print editor_with_args
            call(editor_with_args)
            tmpfile.flush()
            tmpfile.close()

            edited_file = open(tmpfile.name)
            edited_content = edited_file.read()
            edited_file.close()

            os.unlink(tmpfile.name)

            return initial_content, edited_content


class Settings(dict):
    def __init__(self):
        super(Settings, self).__init__()
        if self.check_config_file():
            self.read_config()
            self.validate_settings()

    def read_config(self):
        booleans = ['verbose']
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        options = config.options('defaults')
        for option in options:
            if option in booleans:
                self[option] = config.getboolean('defaults', option)
            else:
                self[option] = config.get('defaults', option)

        self['editor'] = self.get('force_editor', None) or os.environ.get('EDITOR', 'vim')

        if self.get('mediawiki_url') and not self.get('mediawiki_api_url'):
            self['mediawiki_api_url'] = urljoin(self['mediawiki_url'], 'api.php')

    def check_config_file(self):
        if not os.path.isfile(CONFIG_FILE):
            raise Exception(u'Config file %s is missing.'%CONFIG_FILE)
        return True

    def validate_settings(self):
        if not self.get('mediawiki_url', None):
            raise Exception("Config directive 'mediawiki_url' is empty of missing. "
                            "You must provide URL to your mediawiki installation.")

settings = Settings()


class ApiClient(object):
    BASE_URL = settings['mediawiki_api_url']

    def __init__(self):
        self.session = requests.Session()
        self.editor = MediaWikiEditor()
        self.api_login()

    def get_url(self, **kwargs):
        """
        helper function for getting a specific API url
        """
        url = furl.furl(self.BASE_URL).add({'format': 'json'}).add(kwargs)
        return url

    def _get_context(self, **kwargs):
        params = {'format': 'json'}
        params.update(**kwargs)
        return params

    def get_base_request(self, **kwargs) -> requests.Request:
        """
        creates a Request object with all the required headers set.
        Use this function to create new Requests.
        """
        req = requests.Request(**kwargs)

        if not req.url:
            req.url = self.BASE_URL

        # Handle HTTP basic authentication
        if settings.get('http_auth_username', None) and settings.get('http_auth_password', None):
            username = settings['http_auth_username']
            password = settings['http_auth_password']
            req.auth = username, password

        return req

    def execute_request(self, request: requests.Request) -> requests.Response:
        """
        Use this function to execute all Api requests
        """
        prepared = self.session.prepare_request(request)
        resp = self.session.send(prepared)
        return resp

    def do_request(self, **request_kwargs) -> requests.Response:
        """
        Convenience function for creating and executing request in one go.
        """
        req = self.get_base_request(**request_kwargs)
        resp = self.execute_request(req)
        return resp

    def api_login(self):
        """
        Performs the authentication to the mediawiki installation.
        Authentication is somewhat convoluted. Steps
        1. request a token
        2. authenticate using username, password and token
        """

        # Handle Mediawiki authentication
        if settings.get('mediawiki_username', None) and settings.get('mediawiki_password', None):
            username = settings['mediawiki_username']
            password = settings['mediawiki_password']

            # get token
            context = self._get_context(lgname=username)
            login_url = self.get_url(action='login', format='json')
            response = self.do_request(method='POST', data=context, url=login_url)

            # perform the real log in with the token
            if response.status_code == 200:
                login_details = response.json()['login']

                context = self._get_context(lgname=username, lgpassword=password, lgtoken=login_details['token'])
                response = self.do_request(method='POST', data=context, url=login_url)
                resp_data = response.json()['login']
                if resp_data['result'] != 'Success':
                    raise Exception("Unable to log in", response.json())
            else:
                raise('Unable to log in', response)

    def save_article(self, title, content, token):
        """
        Creates new revision for a given article.
        """
        print("Saving {}.".format(title))
        url = self.get_url(action='edit')
        context = self._get_context(text=content, title=title, summary='PyWiki edit', token=token)
        resp = self.do_request(method='POST', data=context, url=url)
        # TODO validate

    def upload_file(self, filepath, alt_filename=None):
        filename = alt_filename or os.path.split(filepath)[1]
        url = self.get_url(action='upload')
        file = open(filepath, 'rb')
        token = self.get_token('files', 'edit')
        context = self._get_context(filename=filename, token=token, ignorewarnings=True)
        resp = self.do_request(method='POST', url=url, data=context, files={'file': file.read()})
        uploaded_file_url = resp.json()['upload']['imageinfo']['url']
        return uploaded_file_url
        # TODO validate

    def get_token(self, title, token_type):
        article_url = self.get_url(action='query', prop='info', titles=title, intoken=token_type)
        resp = self.do_request(method='GET', url=article_url).json()
        edit_token = list(resp['query']['pages'].values())[0]['edittoken']
        return edit_token

    def mv(self, title, new_title):
        url = self.get_url(**{'action': 'move', 'from': title, 'to': new_title})
        mv_token = self.get_token(title, token_type='move')
        context = self._get_context(token=mv_token, noredirect=True)
        resp = self.do_request(method='POST', url=url, data=context)
        #TODO validate

    def search(self, phrase):
        search_url = self.get_url(action='query', list='search', srsearch=phrase, srwhat='text')
        resp = self.do_request(method='GET', url=search_url)

        if resp.status_code == 200:
            return resp.json()['query']['search']
        raise Exception('Search failed', resp)

    def get_page_content(self, title) -> tuple:
        article_url = self.get_url(action='query', prop='info|revisions', titles=title, rvprop='content',
                                   rvlimit=1, intoken='edit')
        resp = self.do_request(method='GET', url=article_url).json()
        first_page = list(resp['query']['pages'].values())[0]
        content = ''
        if 'revisions' in first_page:
            content = first_page['revisions'][0]['*']
        edit_token = first_page['edittoken']
        return content, edit_token

    def display_article(self, title) -> tuple:
        """
            Display article for given title in an EDITOR.
            Returns a tuple of (initial_content, new_content)
        """
        page, edit_token = self.get_page_content(title)
        old_content, new_content = self.editor.open_article(page, title)

        return old_content, new_content, edit_token

    def append_to_article(self, title, text_to_append) -> str:
        page, edit_token = self.get_page_content(title)
        new_content = page + text_to_append
        return new_content, edit_token


class PyWikiCommands(cmd.Cmd):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt = '\nWiki command: '
        self.api = ApiClient()
        self.last_search_query = None
        self.last_search_results = None

    def do_search(self, keyword, quiet=False):
        """ Search for a keyword
        """
        self.last_search_query = keyword
        self.last_search_results = self.api.search(self.last_search_query)
        if not quiet:
            print('Searching for', self.last_search_query)
        self.display_search_list()

    def display_search_list(self):
        """ Display the last search result """
        if not self.last_search_results:
            print('No results for "%s"' % self.last_search_query)
        else:
            # directly display the page
            # print(self.last_search_results)
            if len(self.last_search_results) == 1:
                print('Perfect hit. Opening', self.last_search_query)
                self.do_display_search_result(0)
            else:
                for index, result in enumerate(self.last_search_results, start=1):
                    print(index, result['title'], '\n', html2text.html2text(result['snippet']))

    def do_go(self, title):
        """ go to a specified page. Type "go <pagetitle>" """
        old_content, new_content, edit_token = self.api.display_article(title)
        if old_content != new_content:
            self.api.save_article(title, new_content, edit_token)

    def do_display_search_result(self, index):
        """ displays the article specified by the index in the search list  """
        try:
            index = int(index) - 1 # we enumerated starting on 1
            hit = self.last_search_results[index]
            title = hit['title']
        except IndexError:
            print('Wrong index - try again')
        else:
            print('Opening', title)
            self.do_go(hit['title'])

    def do_append_to_article_and_save(self, title, text_to_append):
        """
        appends text to the bottom of an article and saves
        """
        text_to_append = '\n' + text_to_append
        new_content, edit_token = self.api.append_to_article(title, text_to_append)
        self.api.save_article(title, new_content, edit_token)

    def append_to_article_and_open(self, title, text_to_append):
        text_to_append = '\n' + text_to_append
        new_content, edit_token = self.api.append_to_article(title, text_to_append)
        old_content, new_content = self.api.editor.open_article(new_content, title)

        if old_content != new_content:
            self.api.save_article(title, new_content, edit_token)

    def do_log_and_save(self, page_name, text_to_log):
        """
        Log is the same as append, but it adds a datetime in front of the text
        """
        now = "{:%Y-%m-%d %H:%M} ".format(datetime.datetime.now())
        text_to_log = now + text_to_log
        self.do_append_to_article_and_save(page_name, text_to_log)

    def do_cat(self, title):
        """
        simply print the content of the article
        """
        content, token = self.api.get_page_content(title)
        print(content)

    def do_mv(self, title, new_title):
        """ rename article """
        self.api.mv(title, new_title)

    def do_upload_file(self, filepath, alt_filename=''):
        """
        Upload a new file
        """
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            print(u"File path \"{}\" doesn't exist - nothing uploaded".format(filepath))
        else:
            # token = self.api.get_token(title, token_type='edit')
            uploaded_file_url = self.api.upload_file(filepath, alt_filename)
            print("File uploaded. {}".format(uploaded_file_url))

    def do_EOF(self, line):
        """ quit """
        print()
        '\nbye'
        return True

    def precmd(self, line):
        if not line or len(line) == 0:
            return line

        cmd = line.split()[0]

        if line.startswith('/'):
            line = 'search ' + line[1:]
        elif cmd.isnumeric():
            line = 'display_search_result ' + cmd

        return line

    def postloop(self):
        print()


def run(args):
    m = PyWikiCommands()

    stdin_data = None
    interactive = False

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read()

        tty = open('/dev/tty', 'r')
        os.dup2(tty.fileno(), 0)

    if args['<article_name>']:

        if args['append']:
            if args['<text>']:
                text_to_append = args['<text>']
                m.do_append_to_article_and_save(args['<article_name>'], text_to_append)
        elif args['log']:
            if args['<text>']:
                text_to_log = args['<text>']
                m.do_log_and_save(args['<article_name>'], text_to_log)
        elif args["mv"]:
            m.do_mv(args['<article_name>'], args['<new_name>'])
        elif stdin_data is not None:
            m.append_to_article_and_open(args['<article_name>'], stdin_data)
        elif args['cat']:
            m.do_cat(args['<article_name>'])
        elif args['<article_name>'][0] == "/":  # search
            m.do_search(args['<article_name>'][1:])
            interactive = True
        else:
            # just open article
            m.do_go(args['<article_name>'])
            interactive = True
    elif args['upload']:
            m.do_upload_file(args['<filepath>'], args['<alt_filename>'])
    else:
        interactive = True

    if interactive:
        # and go to interactive mode
        a = m.cmdloop()
