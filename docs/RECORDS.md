# Experiment record v1

The executable validator is `researchos_rf/records.py`. Duplicate JSON keys, NaN and Infinity are rejected. Booleans cannot replace numbers. Unknown metadata is retained.

| Field | Contract |
| --- | --- |
| schema_version | Integer 1 |
| id | 1–80 lowercase letters/digits/underscores/hyphens, starting alphanumeric |
| title, owner, hypothesis | Nonempty strings |
| protocol_reference, differentiation | Nonempty versioned protocol and honest novelty/overlap notes |
| data_kind | synthetic, simulation or experimental; describes inputs |
| link | Link conditions below |
| bands | 1–20 unique band objects |
| sensing | Bandwidth/delay assumptions below |
| measurements | Array, possibly empty for nonexperimental inputs |
| evidence | Evidence declarations |

`link`: tx_power_dbm, tx_gain_dbi, rx_gain_dbi, required_snr_db (finite ±300); system_loss_db and noise_figure_db (0–300); positive bandwidth_mhz, temperature_K and aperture_m; distances_m array; nonempty assumption_reference. See model bounds.

Every band has unique safe `id` with the same format as a record ID, nonempty `label`, frequency_ghz (0.1–300), and extra_attenuation_db_km (0–1000).

`sensing`: bandwidths_mhz array, assumed_round_trip_delay_ns, sample_rate_mhz, and nonempty assumption_reference. The delay is declared, not acquired or inferred from a waveform.

Every measurement has nonempty metric/unit/method, finite value between −10¹⁵ and 10¹⁵, finite nonnegative uncertainty, and evidence_ids referring to declarations. Experimental records require at least one measurement and evidence file, with a reference on each measurement. State coverage/confidence, calibration, acquisition conditions and uncertainty interpretation in method/metadata. This is traceability enforcement, not validation of the measurement.

Every evidence declaration has unique nonempty id, unique relative path, lowercase 64-character sha256, and nonempty description. Paths cannot be absolute, drive paths, traversal or symlinks outside the record directory. Use `researchos-rf hash <file>`. The runner checks and captures the bytes; the manifest maps generated bundle filenames to original evidence IDs. Keep raw measurements, protocols and calibration records where available.

Existing run directories cannot be overwritten. Verification checks artifact hashes, evidence consistency and reproduction of results/report/link CSV. Original files may be relocated after capture, since their bytes are in the bundle. Browser exports are summaries and record JSON, not complete CLI bundles.
