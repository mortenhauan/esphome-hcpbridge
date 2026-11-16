"""Compile the production timestamp methods against a fake clock."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RequestAgeTest(unittest.TestCase):
    def test_clock_and_rollover(self):
        source = (ROOT / 'components/hcpbridge/hoermann.cpp').read_text()
        def method(signature):
            start = source.index(signature)
            return source[start:source.index('\n}', start) + 2]
        code = r'''
#include <atomic>
#include <cstdint>
#include <cassert>
static uint32_t clock_ms;
uint32_t millis() { return clock_ms; }
class HoermannState {
 public:
  std::atomic<uint32_t> lastModbusRespone{0};
  std::atomic<bool> received_request_{false};
  void recordModbusResponse();
  long responseAge();
};
'''
        code += method('void HoermannState::recordModbusResponse()')
        code += '\n' + method('long HoermannState::responseAge()')
        code += r'''
int main() {
  HoermannState state;
  assert(state.responseAge() == -1);
  state.recordModbusResponse(); // Valid request at millis == 0.
  assert(state.responseAge() == 0);
  clock_ms = 1999;
  assert(state.responseAge() == 1);
  clock_ms = 2000;
  assert(state.responseAge() == 2);
  clock_ms = UINT32_MAX - 499;
  state.recordModbusResponse();
  clock_ms = 500;
  assert(state.responseAge() == 1);
  state.recordModbusResponse();
  assert(state.responseAge() == 0);
}
'''
        compiler = shutil.which('clang++') or shutil.which('g++')
        self.assertIsNotNone(compiler, 'A C++ compiler is required')
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'test.cpp'
            binary = Path(tmp) / 'test'
            src.write_text(code)
            subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror',
                            str(src), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
