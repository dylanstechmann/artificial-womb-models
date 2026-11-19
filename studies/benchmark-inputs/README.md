# Synthetic benchmark inputs

These are versioned outputs of this repository used by the alarm studies. Each archive contains the original fixture configuration, report, calibration and evaluation records, reproduction plan and receipt. The archives contain simulated data. All clocks and thresholds are dimensionless.

| Archive | Source | Simulations | Archive SHA-256 |
|---|---|---:|---|
| [Shared threshold calibration](fault-benchmark-86087d7.zip) | [86087d7](https://github.com/dylanstechmann/artificial-womb-models/commit/86087d74c8c69c4bd569acfcaa4667c5ffbb353d) | 792 | `53069129fa73baf7b443cd125c261462dfbebf104110dd2fa0c72c9bb9933843` |
| [Separate actuator threshold calibration](actuator-thresholds-83856bd.zip) | [83856bd](https://github.com/dylanstechmann/artificial-womb-models/commit/83856bdfefe84323f3272f907ec8b7307b413ffc) | 984 | `aacf3d4c98d718c5585519c691842a6b04df16f6229b9a6f6822062e694af239` |

The [confirmation comparison](../alarm-confirmation/REPORT.md) and [persistence comparison](../alarm-persistence/REPORT.md) replay the fitted actuator thresholds with disjoint evaluation noise seeds. Each provides a run-level CSV and the command used to regenerate it.
