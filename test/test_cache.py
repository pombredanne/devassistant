import os
import time

from devassistant.cache import Cache
from devassistant import settings
from devassistant.yaml_assistant_loader import YamlAssistantLoader

# the paths in this dicts are truncated to make tests pass in any location
# (if not truncated, they contain e.g. home dir on your machine, etc.)
# therefore we need a special comparison method in class below
correct_cache = \
{'creator': {'c': {'attrs': {'args': {'foo': {'flags': ['-f', '--foo'],
                                              'help': 'Help for foo parameter.'}},
                             'description': 'C Language Tool description...',
                             'fullname': 'C Language Tool',
                             'template_dir': 'test/fixtures/templates'},
                   'snippets': [],
                   'source': 'test/fixtures/assistants/creator/c.yaml',
                   'subhierarchy': {'d': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'},
                                                             'python': {'flags': ['mock'],
                                                                        'help': 'Display python version',
                                                                        'nargs': '?'},
                                                             'some_arg': {'flags': ['-s',
                                                                                    '--some-arg']}},
                                                    'description': '',
                                                    'fullname': 'D Language Tool',
                                                    'template_dir': 'test/fixtures/templates'},
                                          'snippets': ['snippet1'],
                                          'source': 'test/fixtures/assistants/creator/c/d.yaml',
                                          'subhierarchy': {}},
                                    'e': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'}},
                                                    'description': '',
                                                    'fullname': 'E Language Tool',
                                                    'template_dir': 'test/fixtures/templates'},
                                          'snippets': [],
                                          'source': 'test/fixtures/assistants/creator/c/e.yaml',
                                          'subhierarchy': {}}}},
             'f': {'attrs': {'args': {'name': {'flags': ['-n', '--name'],
                                               'help': 'Name of project to create'}},
                             'description': '',
                             'fullname': 'F Language Tool',
                             'template_dir': 'test/fixtures/templates'},
                   'snippets': [],
                   'source': 'test/fixtures/assistants/creator/f.yaml',
                   'subhierarchy': {'g': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'}},
                                                    'description': '',
                                                    'fullname': 'G Language Tool',
                                                    'template_dir': 'test/fixtures/templates'},
                                          'snippets': [],
                                          'source': 'test/fixtures/assistants/creator/f/g.yaml',
                                          'subhierarchy': {}}}}},
 'modifier': {},
 'preparer': {}}

class TestCache(object):
    cf = settings.CACHE_FILE

    def setup_method(self, method):
        if os.path.exists(self.cf):
            os.unlink(self.cf)
        self.cch = Cache()

    def create_or_refresh_cache(self, roles=settings.ASSISTANT_ROLES, assistants='assistants'):
        for role in roles:
            dirs =[os.path.join(d, assistants, role) for d in settings.DATA_DIRECTORIES]
            fh = YamlAssistantLoader.get_assistants_file_hierarchy(dirs)
            self.cch.refresh_role(role, fh)

    def datafile_path(self, path):
        """Assumes that settings.DATA_DIRECTORIES[0] is test/fixtures"""
        return os.path.join(settings.DATA_DIRECTORIES[0], path)

    def touch_file(self, path):
        os.utime(self.datafile_path(path), None)

    def assert_cache_newer(self, path):
        assert os.path.getctime(self.cch.cache_file) > os.path.getctime(self.datafile_path(path))

    def assert_cache_content(self, expected, actual):
        assert len(expected) == len(actual)
        for k, v in actual.items():
            assert k in expected
            if k in ['source', 'template_dir']:
                assert v.endswith(expected[k])
            else:
                if isinstance(v, dict):
                    self.assert_cache_content(expected[k], v)
                else:
                    assert expected[k] == v

    def test_cache_has_proper_format_on_creation(self):
        self.create_or_refresh_cache()
        self.assert_cache_content(correct_cache, self.cch.cache)

    def test_cache_refreshes_if_assistant_touched(self):
        self.create_or_refresh_cache()
        time.sleep(0.1)

        p = 'assistants/creator/c.yaml'
        self.touch_file(p)
        self.create_or_refresh_cache()
        self.assert_cache_newer(p)

    def test_cache_refreshes_if_snippet_touched(self):
        self.create_or_refresh_cache()
        time.sleep(0.1)

        p = 'snippets/snippet1.yaml'
        self.touch_file(p)
        self.create_or_refresh_cache()
        self.assert_cache_newer(p)

    def test_cache_doesnt_refresh_if_not_needed(self):
        self.create_or_refresh_cache()
        created = os.path.getctime(self.cch.cache_file)
        time.sleep(0.1)
        self.create_or_refresh_cache()
        assert created == os.path.getctime(self.cch.cache_file)
