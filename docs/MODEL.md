# Free-space link and bandwidth/delay model v1

## Link budget

Constants are c = 299792458 m/s and k = 1.380649×10⁻²³ J/K. Frequency is entered in GHz, distance and aperture in meters, receiver bandwidth in MHz, temperature in K, antenna gains in dBi and powers in dBm.

- Wavelength λ = c/f.
- Free-space loss = 20 log10(4πd/λ).
- Declared extra loss = extra attenuation in dB/km × distance/1000.
- Received power = transmit power + transmit gain + receive gain − system loss − free-space loss − extra loss.
- Receiver noise = 10 log10(kTB / 0.001) + noise figure, evaluated in log space.
- SNR = received power − receiver noise. Margin = SNR − declared required SNR.
- Ideal AWGN Shannon bound = B log2(1 + 10^(SNR/10)); displayed in Mbit/s, evaluated with a stable log-sum expression.

The conventional kTB/noise-figure approximation is used; noise figure is an additive receiver factor with declared temperature assumptions, not a calibrated receiver noise-temperature/cascade model. The app does not infer gain from aperture. Gains stay fixed across bands unless the owner supplies separate records. Real fixed-aperture gain often changes with frequency; do not interpret this fixed-gain comparison as a fixed-aperture hardware prediction.

A screening boundary is max(λ, 2D²/λ), where D is the declared largest antenna aperture. Distances below it are flagged `outside-far-field-model`; raw hypothetical values remain in exports, but the declared SNR threshold assessment is withheld and app charts omit those points. Passing the screen does not validate the antenna, propagation regime or measurement setup.

Limits: 1–20 bands, frequency 0.1–300 GHz, 1–100 distances from 10⁻⁶–10⁹ m, extra attenuation 0–1000 dB/km and link bandwidth at most 100000 MHz. Signed link quantities are bounded to ±300 dB/dBm/dBi. Nonfinite derived values are rejected.

No gas/rain/oxygen absorption, blockage, diffraction, multipath, polarization loss, fading, beam alignment, interference or real antenna/transceiver is modeled beyond explicitly declared losses. Extra attenuation is a placeholder, not an atmospheric model. The Shannon value is a theoretical AWGN bound, not application throughput, modulation performance or evidence of a functioning link. No uncertainty is propagated.

## Ideal sensing arithmetic

Ideal bandwidth-limited monostatic range resolution = c/(2B). Assumed range = cτ/2 from a user-supplied round-trip delay τ. Nearest sample index = floor(τ × sample rate + 0.5), so exact half-bin ties round upward. Quantized range uses that index's delay. Sample range-bin spacing = c/(2 sample rate).

No waveform, matched filter, target echo, ambiguity function, detection threshold or false-alarm control is implemented. Resolution, sampling-bin spacing, accuracy and measurement uncertainty are different concepts. These arithmetic quantities are not a demonstration of any of them in hardware. Quantized delay may lie just beyond the assumed delay; it is simply the nearest sampling bin, not a measured result.

Sensing bandwidths and sample rate support 10⁻⁶–100000 MHz; assumed delay is 0–10⁹ ns. Values describe an ideal vacuum/constant-speed monostatic convention, not a propagation-calibrated range estimate.

## Measurement and reproduction

Declared measurements are retained separately without fitting or validating them. The same synthetic/idealized outputs are computed even for experimental input records. Experimental labels require traceable measurements and evidence but do not establish authenticity.

Python and JavaScript are tested for numerical parity over normal, near-field and half-sample cases. Floating-point differences can affect boundary decisions. Bundle verification recomputes exact results under the current runtime; preserve Python version and runner revision for long-lived studies. Hashes are not signatures: replacing all inputs/hashes can forge a self-consistent bundle.
