
import pytest

from click.testing import CliRunner
from nzssdt_2023.scripts.version_cli import cli as version


### some fixtures in a temporary resources folder



### the actual tests ...

def test_ls():
  runner = CliRunner()
  result = runner.invoke(version, ['ls'])
  assert result.exit_code == 0
  assert "VersionInfo(version_id='1'" in result.output

def test_ls_verbose():
  runner = CliRunner()
  result = runner.invoke(version, ['ls', '--verbose'])
  assert result.exit_code == 0
  assert 'Resources path:' in result.output
  assert "VersionInfo(version_id='1'" in result.output

@pytest.mark.skip('WIP - need fixture setup')
def test_init():
  runner = CliRunner()
  result = runner.invoke(version, ['init', 'MY_NEW_VERSION', '--verbose'])
  print( result.output )
  assert result.exit_code == 0
  assert "VersionInfo(version_id='MY_NEW_VERSION'" in result.output
