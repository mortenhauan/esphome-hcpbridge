"""Validate the full board package and assert that our component wins precedence."""
from pathlib import Path
from esphome.core import CORE
from esphome.config import read_config

ROOT = Path(__file__).resolve().parents[1]
CORE.config_path = ROOT / 'tests/merged-device.yaml'
assert read_config({}) is not None, 'Merged configuration failed'
import esphome.components.hcpbridge as bridge
assert Path(bridge.__file__).resolve() == ROOT / 'components/hcpbridge/__init__.py', bridge.__file__
print('Merged configuration valid; fork component selected')
