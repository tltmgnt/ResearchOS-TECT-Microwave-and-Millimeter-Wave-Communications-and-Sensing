"""Idealized free-space RF link budget and bandwidth/delay arithmetic."""
import math
from .records import dumps,require,validate
C=299792458.0
K=1.380649e-23
LIMITATIONS=("Idealized planning calculations only. Free-space far-field loss, declared fixed antenna gains and extra attenuation, and kTB receiver noise are assumed. Shannon values are AWGN upper bounds, not measured throughput. Sensing uses bandwidth/delay arithmetic, not waveform processing or validated detection. No RF hardware, spectrum access, multipath, blockage, rain/gas model, beam alignment, interference or field validation is implemented. No novelty, feasibility or DARPA compliance is established.")


def analyze(record):
    r=validate(record);l=r["link"]
    noise=30+10*(math.log10(K)+math.log10(l["temperature_K"])+math.log10(l["bandwidth_mhz"]*1e6))+l["noise_figure_db"]
    # Equivalent to 10 log10(kTB / 0.001) + NF, evaluated in log space.
    rows=[]
    for b in r["bands"]:
        wavelength=C/(b["frequency_ghz"]*1e9)
        far_field=2*l["aperture_m"]**2/wavelength
        require(math.isfinite(far_field),"far-field distance overflow")
        for d in l["distances_m"]:
            fspl=20*(math.log10(4*math.pi)+math.log10(d)-math.log10(wavelength))
            extra=b["extra_attenuation_db_km"]*d/1000
            received=l["tx_power_dbm"]+l["tx_gain_dbi"]+l["rx_gain_dbi"]-l["system_loss_db"]-fspl-extra
            snr=received-noise
            domain=d>=max(far_field,wavelength)
            gamma_log=snr*math.log(10)/10
            # Stable log2(1+exp(x)) without overflowing high-SNR cases.
            spectral=(gamma_log+math.log1p(math.exp(-gamma_log)) if gamma_log>0 else math.log1p(math.exp(gamma_log)))/math.log(2)
            row={"band_id":b["id"],"frequency_ghz":b["frequency_ghz"],"distance_m":d,"wavelength_m":wavelength,
                 "free_space_loss_db":fspl,"extra_loss_db":extra,"received_power_dbm":received,"noise_power_dbm":noise,"snr_db":snr,
                 "margin_db":snr-l["required_snr_db"],"shannon_upper_bound_mbps":l["bandwidth_mhz"]*spectral,
                 "one_way_delay_ns":d/C*1e9,"far_field_boundary_m":max(far_field,wavelength),
                 "domain_status":"within-declared-far-field" if domain else "outside-far-field-model",
                 "threshold_status":("meets-declared-snr" if snr>=l["required_snr_db"] else "below-declared-snr") if domain else "not-assessed-outside-domain"}
            dumps(row);rows.append(row)
    s=r["sensing"];sample_count=s["assumed_round_trip_delay_ns"]*s["sample_rate_mhz"]/1000
    quantized=math.floor(sample_count+.5);delay=quantized*1000/s["sample_rate_mhz"]
    sensing={"assumed_round_trip_delay_ns":s["assumed_round_trip_delay_ns"],"assumed_range_m":C*s["assumed_round_trip_delay_ns"]*1e-9/2,
             "nearest_sample_index":quantized,"quantized_delay_ns":delay,"quantized_range_m":C*delay*1e-9/2,
             "sample_range_bin_m":C/(2*s["sample_rate_mhz"]*1e6),
             "bandwidth_results":[{"bandwidth_mhz":b,"ideal_range_resolution_m":C/(2*b*1e6)} for b in s["bandwidths_mhz"]],
             "status":"assumed-delay-arithmetic-no-detection"}
    result={"analysis":"free-space-link-and-bandwidth-delay-v1","runner_version":"0.1.0","input_data_kind":r["data_kind"],
            "output_kind":"idealized-calculation","link_results":rows,"sensing_results":sensing,"declared_measurements":r["measurements"],"limitations":LIMITATIONS}
    dumps(result);return result
