"""RF experiment records and strict JSON handling."""
import hashlib
import json
import math
import re
from pathlib import Path


class ValidationError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ValidationError(message)


def dumps(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def parse_json(data):
    def constant(value):
        raise ValidationError(f"non-finite JSON constant: {value}")
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, f"duplicate JSON key: {k}")
            result[k] = v
        return result
    return json.loads(data, parse_constant=constant, object_pairs_hook=unique)


def read_json(path):
    return parse_json(Path(path).read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(v, name):
    require(isinstance(v, str) and bool(v.strip()), f"{name} must be a nonempty string")


def integer(v, name, minimum=0, maximum=10**12):
    require(type(v) is int and minimum <= v <= maximum, f"{name} must be an integer in [{minimum}, {maximum}]")


def number(v, name, positive=False):
    require(type(v) in (int, float), f"{name} must be numeric")
    try:
        finite = math.isfinite(v)
    except OverflowError:
        finite = False
    require(finite and (v > 0 if positive else v >= 0), f"{name} must be finite and {'positive' if positive else 'nonnegative'}")


def safe_path(value):
    text(value, "evidence path")
    require(not Path(value).is_absolute() and "\\" not in value and not re.match(r"^[A-Za-z]:", value)
            and not any(p in (".", "..") for p in value.split("/")), "evidence path must be relative without traversal")
    return Path(value)


def evidence_bytes(root, path):
    root = Path(root).resolve()
    dest = (root / safe_path(path)).resolve()
    require(dest.is_relative_to(root), "evidence resolves outside record directory")
    return dest.read_bytes()


def signed(v,name,minimum=-300,maximum=300):
    require(type(v) in (int,float) and minimum <= v <= maximum, f"{name} must be finite in [{minimum},{maximum}]")


def validate(r):
    require(isinstance(r,dict), "record must be an object")
    require(type(r.get("schema_version")) is int and r["schema_version"]==1, "schema_version must be integer 1")
    require(isinstance(r.get("id"),str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}",r["id"])), "invalid record id")
    for k in ("title","owner","hypothesis","protocol_reference","differentiation"):
        text(r.get(k),k)
    require(r.get("data_kind") in ("synthetic","simulation","experimental"),"invalid input basis")
    link=r.get("link")
    require(isinstance(link,dict),"link must be an object")
    for k in ("tx_power_dbm","tx_gain_dbi","rx_gain_dbi","required_snr_db"):
        signed(link.get(k),k)
    for k in ("system_loss_db","noise_figure_db"):
        number(link.get(k),k)
        require(link[k]<=300,f"{k} must be <=300")
    for k in ("bandwidth_mhz","temperature_K","aperture_m"):
        number(link.get(k),k,True)
    require(link["bandwidth_mhz"]<=100000,"link bandwidth must be <=100000 MHz")
    distances=link.get("distances_m")
    require(isinstance(distances,list) and 1<=len(distances)<=100,"provide 1–100 distances")
    for d in distances:
        number(d,"distance_m",True)
        require(1e-6<=d<=1e9,"distance must be in [1e-6,1e9] m")
    text(link.get("assumption_reference"),"link assumption_reference")
    bands=r.get("bands")
    require(isinstance(bands,list) and 1<=len(bands)<=20,"provide 1–20 bands")
    ids=set()
    for b in bands:
        require(isinstance(b,dict),"band must be an object")
        require(isinstance(b.get("id"),str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}",b["id"])),"invalid band id")
        require(b["id"] not in ids,"duplicate band id")
        ids.add(b["id"])
        text(b.get("label"),"band label")
        number(b.get("frequency_ghz"),"frequency_ghz",True)
        require(.1<=b["frequency_ghz"]<=300,"frequency must be 0.1–300 GHz")
        number(b.get("extra_attenuation_db_km"),"extra_attenuation_db_km")
        require(b["extra_attenuation_db_km"]<=1000,"extra attenuation must be <=1000 dB/km")
    sensing=r.get("sensing")
    require(isinstance(sensing,dict),"sensing must be an object")
    bandwidths=sensing.get("bandwidths_mhz")
    require(isinstance(bandwidths,list) and 1<=len(bandwidths)<=100,"provide 1–100 sensing bandwidths")
    for b in bandwidths:
        number(b,"sensing bandwidth",True)
        require(1e-6<=b<=100000,"sensing bandwidth must be 1e-6–100000 MHz")
    number(sensing.get("assumed_round_trip_delay_ns"),"assumed_round_trip_delay_ns")
    require(sensing["assumed_round_trip_delay_ns"]<=1e9,"delay must be <=1e9 ns")
    number(sensing.get("sample_rate_mhz"),"sample_rate_mhz",True)
    require(1e-6<=sensing["sample_rate_mhz"]<=100000,"sample rate must be 1e-6–100000 MHz")
    text(sensing.get("assumption_reference"),"sensing assumption_reference")
    evidence=r.get("evidence")
    require(isinstance(evidence,list),"evidence must be an array")
    refs,paths=set(),set()
    for e in evidence:
        require(isinstance(e,dict),"evidence entry must be an object")
        for k in ("id","description"):
            text(e.get(k),k)
        safe_path(e.get("path"))
        require(e["id"] not in refs and e["path"] not in paths,"duplicate evidence id/path")
        refs.add(e["id"]);paths.add(e["path"])
        require(isinstance(e.get("sha256"),str) and bool(re.fullmatch(r"[a-f0-9]{64}",e["sha256"])),"invalid evidence digest")
    measurements=r.get("measurements")
    require(isinstance(measurements,list),"measurements must be an array")
    for m in measurements:
        require(isinstance(m,dict),"measurement must be an object")
        for k in ("metric","unit","method"):
            text(m.get(k),k)
        signed(m.get("value"),"measurement value",-1e15,1e15)
        number(m.get("uncertainty"),"measurement uncertainty")
        links=m.get("evidence_ids")
        require(isinstance(links,list) and all(isinstance(x,str) and x in refs for x in links),"unknown measurement evidence reference")
        require(r["data_kind"]!="experimental" or bool(links),"experimental measurements require evidence references")
    require(r["data_kind"]!="experimental" or bool(measurements) and bool(evidence),"experimental records require measurements and evidence")
    return r
