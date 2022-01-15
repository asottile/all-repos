from __future__ import annotations

import pytest

from all_repos.complete import main

# TODO: some integration tests of completion against the shells (how???)


@pytest.mark.parametrize('opt', ('--bash', '--zsh'))
def test_smoke_doesnt_crash(file_config_files, capsys, opt):
    assert not main(('--config-filename', str(file_config_files.cfg), opt))
    out, _ = capsys.readouterr()
    assert out != ''
