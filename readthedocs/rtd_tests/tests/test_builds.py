import os
import subprocess

from django.test import TestCase
import mock

from readthedocs.doc_builder.environments import LocalEnvironment
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.projects.tasks import UpdateDocsTask

from ..factories.projects_factories import ProjectFactory
from ..mocks.paths import fake_paths_lookup
from ..mocks.environment import EnvironmentMockGroup


class BuildEnvironmentTests(TestCase):

    def setUp(self):
        self.mocks = EnvironmentMockGroup()
        self.mocks.start()

    def tearDown(self):
        self.mocks.stop()

    def test_build(self):
        '''Test full build'''
        project = ProjectFactory(allow_comments=True)
        version = project.versions.all()[0]
        self.mocks.configure_mock('api_versions', {'return_value': [version]})
        self.mocks.configure_mock('api', {
            'get.return_value': {'downloads': "no_url_here"}
        })
        self.mocks.patches['html_build'].stop()

        build_env = LocalEnvironment(project=project, version=version)
        task = UpdateDocsTask()
        task.build_env = build_env
        task.version = version
        task.project = project

        built_docs = task.build_docs(False, False, False)

        # Get command and check first part of command list is a call to sphinx
        self.assertEqual(self.mocks.popen.call_count, 1)
        cmd = self.mocks.popen.call_args_list[0][0]
        self.assertRegexpMatches(cmd[0][0], r'sphinx-build')

    def test_build_respects_pdf_flag(self):
        '''Build output format control'''
        project = ProjectFactory(
            enable_pdf_build=True,
            enable_epub_build=False)
        version = project.versions.all()[0]

        build_env = LocalEnvironment(project=project, version=version)
        task = UpdateDocsTask()
        task.build_env = build_env
        task.version = version
        task.project = project

        built_docs = task.build_docs(False, False, False)

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.pdf_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.epub_build.called)

    def test_build_respects_epub_flag(self):
        '''Test build with epub enabled'''
        project = ProjectFactory(
            enable_pdf_build=False,
            enable_epub_build=True)
        version = project.versions.all()[0]

        build_env = LocalEnvironment(project=project, version=version)
        task = UpdateDocsTask()
        task.build_env = build_env
        task.version = version
        task.project = project

        built_docs = task.build_docs(False, False, False)

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.epub_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.pdf_build.called)

    def test_builder_comments(self):
        '''Normal build with comments'''
        project = ProjectFactory(allow_comments=True)
        version = project.versions.all()[0]
        build_env = LocalEnvironment(version=version, project=project)
        builder_class = get_builder_class(project.documentation_type)
        builder = builder_class(build_env)
        self.assertEqual(builder.sphinx_builder, 'readthedocs-comments')

    def test_builder_no_comments(self):
        '''Test builder without comments'''
        project = ProjectFactory(allow_comments=False)
        version = project.versions.all()[0]
        build_env = LocalEnvironment(version=version, project=project)
        builder_class = get_builder_class(project.documentation_type)
        builder = builder_class(build_env)
        self.assertEqual(builder.sphinx_builder, 'readthedocs')

    def test_build_pdf_latex_failures(self):
        '''Build failure if latex fails'''
        self.mocks.patches['html_build'].stop()
        self.mocks.patches['pdf_build'].stop()

        project = ProjectFactory(
            enable_pdf_build=True,
            enable_epub_build=False)
        version = project.versions.all()[0]
        assert project.conf_dir() == '/tmp/rtd'

        build_env = LocalEnvironment(project=project, version=version)
        task = UpdateDocsTask()
        task.build_env = build_env
        task.version = version
        task.project = project

        # Mock out the separate calls to Popen using an iterable side_effect
        returns = [
            (('', ''), 0),  # sphinx-build html
            (('', ''), 0),  # sphinx-build pdf
            (('', ''), 1),  # latex
            (('', ''), 0),  # makeindex
            (('', ''), 0),  # latex
        ]
        mock_obj = mock.Mock()
        mock_obj.communicate.side_effect = [output for (output, status)
                                            in returns]
        type(mock_obj).returncode = mock.PropertyMock(
            side_effect=[status for (output, status) in returns])
        self.mocks.popen.return_value = mock_obj

        with build_env:
            built_docs = task.build_docs(False, False, False)
        self.assertEqual(self.mocks.popen.call_count, 5)
        self.assertTrue(build_env.failed)

    def test_build_pdf_latex_not_failure(self):
        '''Test pass during PDF builds and bad latex failure status code'''
        self.mocks.patches['html_build'].stop()
        self.mocks.patches['pdf_build'].stop()

        project = ProjectFactory(
            enable_pdf_build=True,
            enable_epub_build=False)
        version = project.versions.all()[0]
        assert project.conf_dir() == '/tmp/rtd'

        build_env = LocalEnvironment(project=project, version=version)
        task = UpdateDocsTask()
        task.build_env = build_env
        task.version = version
        task.project = project

        # Mock out the separate calls to Popen using an iterable side_effect
        returns = [
            (('', ''), 0),  # sphinx-build html
            (('', ''), 0),  # sphinx-build pdf
            (('Output written on foo.pdf', ''), 1),  # latex
            (('', ''), 0),  # makeindex
            (('', ''), 0),  # latex
        ]
        mock_obj = mock.Mock()
        mock_obj.communicate.side_effect = [output for (output, status)
                                            in returns]
        type(mock_obj).returncode = mock.PropertyMock(
            side_effect=[status for (output, status) in returns])
        self.mocks.popen.return_value = mock_obj

        with build_env:
            built_docs = task.build_docs(False, False, False)
        self.assertEqual(self.mocks.popen.call_count, 5)
        self.assertTrue(build_env.successful)
