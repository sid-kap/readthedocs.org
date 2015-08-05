import mock

from readthedocs.doc_builder.environments import LocalEnvironment


class EnvironmentMockGroup(object):
    '''Mock out necessary environment pieces'''

    def __init__(self):
        self.patches = {
            'popen': mock.patch('subprocess.Popen'),
            'process': mock.Mock(),

            'api_versions': mock.patch(
                'readthedocs.projects.models.Project.api_versions'),
            'api': mock.patch('slumber.Resource'),

            'append_conf': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.BaseSphinx.append_conf'),
            'move': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.BaseSphinx.move'),
            'conf_dir': mock.patch(
                'readthedocs.projects.models.Project.conf_dir'),
            'html_build': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.HtmlBuilder.build'),
            'html_move': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.HtmlBuilder.move'),
            'pdf_build': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.PdfBuilder.build'),
            'pdf_move': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.PdfBuilder.move'),
            'epub_build': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.EpubBuilder.build'),
            'epub_move': mock.patch(
                'readthedocs.doc_builder.backends.sphinx.EpubBuilder.move'),
            'glob': mock.patch('readthedocs.doc_builder.backends.sphinx.glob'),

            'update_build': mock.patch.object(LocalEnvironment, 'update_build'),
        }
        self.mocks = {}

    def start(self):
        '''Create a patch object for class patches'''
        for patch in self.patches:
            self.mocks[patch] = self.patches[patch].start()
        self.mocks['process'].communicate.return_value = ('', '')
        self.mocks['process'].returncode = 0
        self.mocks['popen'].return_value = self.mocks['process']
        self.mocks['glob'].return_value = ['/tmp/rtd/foo.tex']
        self.mocks['conf_dir'].return_value = '/tmp/rtd'

    def stop(self):
        for patch in self.patches:
            try:
                self.patches[patch].stop()
            except RuntimeError:
                pass

    def configure_mock(self, mock, args):
        '''Configure object mocks'''
        self.mocks[mock].configure_args(*args)

    def __getattr__(self, name):
        try:
            return self.mocks[name]
        except KeyError:
            raise AttributeError()
