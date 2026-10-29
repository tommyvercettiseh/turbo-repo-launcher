from types import SimpleNamespace
import sys

import pytest
from app.services_fixed import RepoService


def test_failed_fetch_cannot_report_clean(tmp_path, monkeypatch):
    (tmp_path / '.git').mkdir()
    def command(args, *a, **kw):
        if args[1] == 'fetch':
            raise RuntimeError('Network unavailable')
        return ''
    monkeypatch.setattr(RepoService, 'run_command', command)
    info = RepoService.git_info(tmp_path)
    assert info['git_status'] == 'check-failed'
    assert info['sync_checked'] is False
    assert info['sync_error'] == 'Network unavailable'


def test_dirty_work_remains_protected_if_fetch_fails(tmp_path, monkeypatch):
    (tmp_path / '.git').mkdir()
    def command(args, *a, **kw):
        if args[1] == 'status':
            return ' M app.py'
        if args[1] == 'fetch':
            raise RuntimeError('Offline')
        return ''
    monkeypatch.setattr(RepoService, 'run_command', command)
    info = RepoService.git_info(tmp_path)
    assert info['dirty'] is True
    assert info['git_status'] == 'local-changes'
    assert info['sync_checked'] is False


def test_test_button_uses_project_command(tmp_path, monkeypatch):
    (tmp_path / 'turbo-project.json').write_text('{"testing":{"command":"npm test"}}')
    monkeypatch.setattr(RepoService, 'get_repo', lambda slug: {'local_path': str(tmp_path)})
    seen = []
    def run(command, **kwargs):
        seen.append(command)
        return SimpleNamespace(returncode=0, stdout='passed', stderr='')
    monkeypatch.setattr('app.services_fixed.subprocess.run', run)
    assert RepoService.run_tests('web')['ok'] is True
    assert seen == ['npm test']


def test_missing_test_command_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setattr(RepoService, 'get_repo', lambda slug: {'local_path': str(tmp_path)})
    with pytest.raises(RuntimeError, match='Geen testcommando'):
        RepoService.run_tests('web')


def test_legacy_python_projects_keep_their_test_button(tmp_path, monkeypatch):
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests' / 'test_app.py').write_text('def test_app(): pass')
    monkeypatch.setattr(RepoService, 'get_repo', lambda slug: {'local_path': str(tmp_path)})
    seen = []
    monkeypatch.setattr('app.services_fixed.subprocess.run', lambda command, **kw:
                        seen.append(command) or SimpleNamespace(returncode=0, stdout='', stderr=''))
    assert RepoService.run_tests('legacy')['ok']
    assert seen == [[sys.executable, '-m', 'pytest', '-q']]


def test_npm_projects_work_without_a_hub_manifest(tmp_path, monkeypatch):
    (tmp_path / 'package.json').write_text('{"scripts":{"test":"node --test"}}')
    monkeypatch.setattr(RepoService, 'get_repo', lambda slug: {'local_path': str(tmp_path)})
    seen = []
    monkeypatch.setattr('app.services_fixed.subprocess.run', lambda command, **kw:
                        seen.append(command) or SimpleNamespace(returncode=0, stdout='', stderr=''))
    assert RepoService.run_tests('web')['ok']
    assert seen == ['npm test']
