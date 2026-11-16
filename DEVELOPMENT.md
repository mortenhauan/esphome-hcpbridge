# Bus startup and outage diagnostics

Development branch: `codex/bus-startup-diagnostics`.
No hardware test or confirmed fix for the reported HA-restart bus failure yet.

## Changes

- Register all Modbus registers/callbacks before starting the worker. Upstream
  starts the worker first, allowing initialization to race incoming bus requests.
- Initialize optional pin pointers explicitly.
- Fix pointer arithmetic on a string literal in the unknown-function diagnostic.
- Use an atomic request timestamp and receipt flag across tasks. Request age uses
  unsigned 32-bit elapsed time, including across millis rollover; receipt at zero
  is distinct from never having received a request.
- Optional diagnostics package adds uptime, reset reason and last request age.

The existing Connected sensor is not a reliable lost-bus indicator. Request age
includes broadcasts and only proves reception of traffic reaching the Modbus
callback, not successful replies or acceptance by the opener. No active bus scan
or movement command is added. Other shared command/state access still needs review.

## ESPHome setup

Keep your existing board package, device identity, encryption key and Wi-Fi setup.
Add the diagnostics package and override the component source:

```yaml
packages:
  tynet.hcpbridge_e4: github://Tysonpower/HCPBridgeMqtt_tynet/esphome.yaml@main
  hcp_diagnostics: github://mortenhauan/esphome-hcpbridge/packages/diagnostics.yaml@codex/bus-startup-diagnostics

external_components: !override
  - source: github://mortenhauan/esphome-hcpbridge@codex/bus-startup-diagnostics
    components: [hcpbridge]
    refresh: 0s
```

Once a revision is tested, replace the branch with its full commit SHA in both
fork references. The board package and its Modbus library are still floating;
these also need pinning for a fully reproducible release.

## Verification

Run `python3 tests/test_request_age.py` (requires a C++ compiler) and validate/build
`tests/device.yaml` with ESPHome. That build config uses dummy credentials and no
physical device. Tests exercise the actual responseAge/recordModbusResponse method
bodies with a fake clock; they do not simulate UART, FreeRTOS or the motor.

Before hardware use, complete an ESP32 firmware build. Be physically present for
installation because a bridge reboot can require another opener bus scan.
Record uptime, reset reason and bus request age through the bridge web interface
across a short HA restart. HA history alone misses the outage itself. Rising age
with continuous uptime suggests lost traffic; low age can still mask an addressed
polling failure if broadcasts continue. A reset needs reset-cause investigation.
Bus-loop gap instrumentation and protocol traces remain follow-up work.

Rollback by removing the diagnostics package and external_components override,
rebuilding the original board package and rescanning if needed.
