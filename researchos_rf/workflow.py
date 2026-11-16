"""Portable RF experiment bundles with captured evidence and recomputation checks."""
import csv
import io
import platform
import re
import shutil
import tempfile
from pathlib import Path
from .records import dumps, evidence_bytes, parse_json, read_json, require, sha, validate
from .model import analyze


def verify_evidence(record, root):
    captured = []
    for item in record["evidence"]:
        data = evidence_bytes(root, item["path"])
        require(sha(data) == item["sha256"], f"evidence checksum mismatch: {item['path']}")
        captured.append((item, data))
    return captured


def report(record,result):
    lines=[f"# {record['id']}","",record["title"],"",f"Input basis: **{record['data_kind']}**. Output: **idealized calculation**.","",result["limitations"],"","| Band | Distance m | Received dBm | SNR dB | Domain |","| --- | ---: | ---: | ---: | --- |"]
    for r in result["link_results"]:
        lines.append(f"| {r['band_id']} | {r['distance_m']:g} | {r['received_power_dbm']:.6g} | {r['snr_db']:.6g} | {r['domain_status']} |")
    s=result["sensing_results"]
    lines += ["","## Ideal bandwidth and assumed delay", "",f"Assumed round-trip delay: {s['assumed_round_trip_delay_ns']:g} ns; assumed range: {s['assumed_range_m']:.6g} m.",f"Nearest sample: {s['nearest_sample_index']}; quantized range: {s['quantized_range_m']:.6g} m.","", "| Bandwidth MHz | Ideal range resolution m |", "| ---: | ---: |"]
    for row in s["bandwidth_results"]:
        lines.append(f"| {row['bandwidth_mhz']:g} | {row['ideal_range_resolution_m']:.6g} |")
    lines += ["","These are arithmetic quantities, not measured resolution, detection performance or uncertainty.","",f"Declared measurements: {len(record['measurements'])}; retained separately, not fitted or validated.","","## Differentiation","",record["differentiation"]]
    return "\n".join(lines)+"\n"


def link_csv(record,result):
    buf=io.StringIO(newline="")
    writer=csv.DictWriter(buf,fieldnames=list(result["link_results"][0]))
    writer.writeheader();writer.writerows(result["link_results"])
    return buf.getvalue()


def run(path, output):
    path, output = Path(path), Path(output)
    require(not output.exists(), "output exists; use a new run directory")
    raw = path.read_bytes()
    record = validate(parse_json(raw.decode("utf-8")))
    captured = verify_evidence(record, path.parent)
    result = analyze(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".researchos-", dir=output.parent))
    try:
        (staging / "record.json").write_bytes(raw)
        (staging / "results.json").write_text(dumps(result), encoding="utf-8")
        (staging / "report.md").write_text(report(record, result), encoding="utf-8")
        (staging / "link.csv").write_text(link_csv(record, result), encoding="utf-8")
        for i, (_, data) in enumerate(captured):
            dest = staging / "evidence" / f"{i:04d}.bin"
            dest.parent.mkdir(exist_ok=True)
            dest.write_bytes(data)
        files = {p.relative_to(staging).as_posix(): sha(p.read_bytes()) for p in sorted(staging.rglob("*")) if p.is_file()}
        manifest = {"schema_version": 1, "files": files, "python_version": platform.python_version(),
                    "evidence_map": [{"id": e["id"], "bundle_path": f"evidence/{i:04d}.bin"} for i, (e, _) in enumerate(captured)]}
        (staging / "manifest.json").write_text(dumps(manifest), encoding="utf-8")
        output.mkdir()
        for p in staging.iterdir():
            shutil.move(str(p), output / p.name)
    finally:
        shutil.rmtree(staging)
    return result


def verify_bundle(root):
    root = Path(root)
    m = read_json(root / "manifest.json")
    require(isinstance(m, dict) and m.get("schema_version") == 1, "invalid manifest")
    files = m.get("files")
    require(isinstance(files, dict) and {"record.json", "results.json", "report.md", "link.csv"} <= files.keys(), "incomplete manifest")
    for name, expected in files.items():
        require(isinstance(expected, str) and bool(re.fullmatch(r"[a-f0-9]{64}", expected)), "invalid manifest digest")
        require(sha(evidence_bytes(root, name)) == expected, f"bundle checksum mismatch: {name}")
    record = validate(read_json(root / "record.json"))
    result = analyze(record)
    require(read_json(root / "results.json") == result, "numerical results do not reproduce")
    require((root / "report.md").read_text(encoding="utf-8") == report(record, result), "report does not reproduce")
    # Text newline translation is normalized before comparing CSV exports.
    actual_csv = (root / "link.csv").read_text(encoding="utf-8")
    require(actual_csv == link_csv(record, result).replace("\r\n", "\n"), "CSV does not reproduce")
    mapping = [{"id": e["id"], "bundle_path": f"evidence/{i:04d}.bin"} for i, e in enumerate(record["evidence"])]
    require(m.get("evidence_map") == mapping, "invalid evidence map")
    for entry, original in zip(mapping, record["evidence"]):
        require(entry["bundle_path"] in files, "evidence absent from manifest")
        require(sha(evidence_bytes(root, entry["bundle_path"])) == original["sha256"], "captured evidence no longer matches record")
    return m
