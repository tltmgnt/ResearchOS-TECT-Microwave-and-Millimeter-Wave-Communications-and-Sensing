# ResearchOS TECT — Microwave and Millimeter-Wave Communications and Sensing

Independent research workspace for microwave and millimeter-wave communications and sensing, supporting reproducible channel modeling, link-budget analysis, experiment design, prototype evaluation, and evidence-linked assessment of performance, uncertainty, and research differentiation.

## Working implementation

- Multi-band free-space link sweeps: path loss, declared extra attenuation, received power, kTB receiver noise, SNR and owner-defined margin.
- A far-field screening flag, with threshold assessment withheld outside the model domain.
- Ideal AWGN Shannon capacity upper bounds, explicitly distinct from measured throughput.
- Ideal bandwidth-based range resolution, assumed round-trip delay, and sample-quantized range arithmetic.
- Validated experiment records, differentiation/protocol references, signed declared measurements with uncertainty, evidence hashes and portable verified bundles.
- A browser app with editable bands, charts, local records, imports, parameter templates, evidence checks and JSON/CSV/Markdown exports.

The models implement established baseline equations, not a novel RF technique or validated prototype. There is no RF hardware, spectrum access, waveform acquisition, detector, environmental calibration or field validation. No DARPA affiliation, award, endorsement, eligibility or submission is claimed. TECT remains the project identifier without an assumed expansion.

## Quick start

Python 3.10 or newer; no third-party runtime dependencies:

```bash
python -m researchos_rf validate examples/synthetic-rf.json
python -m researchos_rf run examples/synthetic-rf.json --output runs/demo
python -m researchos_rf verify runs/demo
python -m researchos_rf report runs/demo
python -m unittest discover -s tests -v
```

Optional installation:

```bash
python -m pip install .
researchos-rf --help
```

The synthetic fixture compares 6, 28 and 60 GHz at 10, 50, 100 and 500 m. At 6 GHz and 10 m it gives approximately 68.0108 dB free-space loss. At 290 K, 100 MHz bandwidth and 6 dB noise figure, receiver noise is approximately −87.9752 dBm. A declared 20 ns round trip corresponds to 2.99792458 m in vacuum. These are arithmetic checks, not measurements or a working-system claim.

## Browser app

Serve `web/` with `python -m http.server 8000 --directory web`, then open `http://localhost:8000`. Use localhost or HTTPS for modules, workers and Web Crypto. Run `node web/tests/model.test.mjs` for browser-model checks.

Calculations run in a worker. Records stay in the current browser and origin; export regularly. No GitHub, CLI or cross-device synchronization is configured. Record JSON exports work with the CLI. Web result/report exports are summaries, not full CLI evidence bundles. Evidence files are hashed locally, never uploaded or retained; original files must be preserved separately. Imported/reloaded records do not re-verify them.

The form creates synthetic/simulation records. Experimental records may be imported with measurements and evidence declarations, while calculations remain separately labeled idealized output. Reusing parameters in a new template changes experimental input basis to simulation and omits measurements/evidence; the original saved record remains intact.

## Your research workflow

1. Copy the example and assign an ID, owner, hypothesis, protocol reference and honest input basis.
2. Define link conditions, bands and sensing assumptions with explicit units and versioned sources. Review the [model domains](docs/MODEL.md).
3. Document proposed differentiation and related-work/program overlap review. Software tests do not establish novelty.
4. Add declared measurements with method, units, uncertainty and evidence IDs. The model stores these separately without fitting or validating them.
5. Place evidence below the record directory; use `researchos-rf hash <file>` and declare each relative path, digest, description and ID.
6. Validate, run into a new output directory, verify, and review. Existing run directories are rejected.

Source paths cannot escape the record directory, including through symlinks. The runner captures the verified bytes. Hashes establish byte consistency, not authenticity or calibration. Local bundles are ignored by Git; keep credentials and unpublished partner data out of this public repository.

## Bundle contents

| File | Purpose |
| --- | --- |
| `record.json` | Exact original input bytes |
| `results.json` | Link sweep, domain flags, sensing arithmetic, declared measurements and limitations |
| `link.csv` | All band/distance link results |
| `report.md` | Human-readable results, assumptions and differentiation |
| `evidence/0000.bin`, … | Captured original evidence bytes |
| `manifest.json` | File digests, evidence mapping and Python version |

Verification checks hashes, evidence-to-record consistency and reproduction of results/report/CSV. Same inputs and runtime yield identical bundles. This is not a signed or tamper-proof audit service.

## Documentation and CI

- [Equations and limits](docs/MODEL.md)
- [Record contract](docs/RECORDS.md)
- [Research plan](docs/RESEARCH_PLAN.md)
- [Primary sources](docs/SOURCES.md)
- [Contributing](CONTRIBUTING.md)

CI checks JavaScript, web-model tests, Python tests, web/Python parity, installed CLI execution and synthetic bundle upload across Python 3.10–3.13. The existing [license](LICENSE) is preserved.

Private hosted app: https://researchos-tect-mmwave.troturn31.chatgpt.site
