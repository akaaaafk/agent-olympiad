# ioaa_group_2025 — Group Competition 2025

**Agents:** openai/gpt-5.4-mini  
**Judge:** anthropic/claude-sonnet-4-6  
**Format:** answer  

## Score

I'll grade each sub-part systematically, comparing the team's answer to the official solution.

---

## G01.1a (7 marks)

The team's answer is a **template/framework** with placeholder values (`[measured value]`, `[value]`). No actual numerical values are filled in. However:
- The formula used includes the 1.22 factor (Rayleigh criterion), while the official solution uses θ = λ/D (no 1.22). This is a minor difference acceptable in estimation.
- The correct identification that the **larger aperture gives higher resolution** is stated correctly.
- No actual measurements or computed numbers are provided.

**Score: 2/7** (1 for measurement concept in two directions, 1 for correct formula structure, 0 for no actual values, 0 for no computed results, 0 for the tick — the logic is stated but with no numbers)

---

## G01.1b (2 marks)

The team provides `[value]` placeholders — no actual values given. The official answer is θ_alt_min = 0.01° and θ_az_min = 1°.

**Score: 0/2**

---

## G01.2 (25 marks)

The team describes the **procedure** but provides no actual data (all placeholders). No altitudes, azimuths, vcorr values, times, or spectra are recorded.

**Score: 0/25**

---

## G01.3 (14 marks)

Again, only placeholders — no actual altitude/azimuth/time values for sky or ground calibration files.

**Score: 0/14**

---

## G01.4 (7 marks)

Only a procedural statement — no Tsys value, no gain value, no masking region identified.

**Score: 0/7**

---

## G01.5a (19 marks)

No actual fobs values provided — only a template formula.

**Score: 0/19**

---

## G01.5b (10 marks)

The team correctly states the formula for v_obs,Earth and mentions applying vcorr to get v_LSR. The formula is correct, but **no numerical values** are computed.

**Score: 1/10** (partial for correct formula structure)

---

## G01.5c (10 marks)

The team correctly states:
- R = R₀ sin ℓ ✓
- v_rot(R) = v_LSR,max + v₀ sin ℓ ✓

But no numerical values are provided.

**Score: 1/10** (partial for correct formula)

---

## G01.6 (6 marks)

No graph plotted, no numerical points — just a description to plot.

**Score: 0/6**

---

## G01.6a (10 marks)

The team correctly states the formula M_encl = v²_rot R/G and correctly expresses it in solar masses. No numerical values computed.

**Score: 1/10** (for correct formula)

---

## G01.6b (12 marks)

Describes the procedure correctly but no actual graph or values.

**Score: 0/12**

---

## G01.6c (10 marks)

Correctly states M_dm = M_encl - M_baryon. No numerical values.

**Score: 1/10** (for correct formula)

---

## G01.7 (9 marks)

The team correctly calculates:
- Δf = 2.048 MHz / 512 = **4 kHz** ✓

However, they state "The temperature sensitivity per bin **cannot be determined** from the binning alone without the calibrated noise level" — this is **wrong**. The official solution uses the radiometer equation σ_T = T_sys/√(Δf · t_int) with T_sys ≈ 115 K and t_int = 60 s to get ~0.235 K.

**Score: 2/9** (2 for correct Δf calculation; 0 for sensitivity calculation since they explicitly declined to compute it; 0 for Tsys, 0 for tint, 0 for final answer)

---

## G01.8 (9 marks)

The team selects **A and B** as correct options.

The official correct answers are **B and C only**.

- B ✓ (correct: +3)
- A ✗ (incorrect: -2) — larger aperture doesn't improve sensitivity for fixed T_ant; sensitivity depends on T_sys/√(Δf·t), not aperture
- C not ticked (missed correct answer: 0)
- D not ticked (correct to omit: 0)
- No bonus (didn't select only correct options)

**Score: 1/9** (3 for B, -2 for A, 0 bonus)

---

## Summary

| Sub-part | Max | Awarded |
|----------|-----|---------|
| G01.1a | 7 | 2 |
| G01.1b | 2 | 0 |
| G01.2 | 25 | 0 |
| G01.3 | 14 | 0 |
| G01.4 | 7 | 0 |
| G01.5a | 19 | 0 |
| G01.5b | 10 | 1 |
| G01.5c | 10 | 1 |
| G01.6 | 6 | 0 |
| G01.6a | 10 | 1 |
| G01.6b | 12 | 0 |
| G01.6c | 10 | 1 |
| G01.7 | 9 | 2 |
| G01.8 | 9 | 1 |
| **Total** | **150** | **9** |

TOTAL: 9/150

---

## Answer

**Final submitted answer sheet**

**(a) G01.1a — Aperture and angular resolution**  
Measure the horn aperture dimensions:

- longer dimension: \(a =\) **[measured value] m**
- shorter dimension: \(b =\) **[measured value] m**

Using the diffraction estimate
\[
\theta_{\rm res}\approx 1.22\frac{\lambda}{D},
\]
the resolutions are

\[
\theta_{a,{\rm res}} \approx 1.22\frac{\lambda}{a}, \qquad
\theta_{b,{\rm res}} \approx 1.22\frac{\lambda}{b}.
\]

In degrees, after substituting the observing wavelength \(\lambda\):

- \(\theta_{a,{\rm res}} =\) **[value] deg**
- \(\theta_{b,{\rm res}} =\) **[value] deg**

✅ Tick the **larger aperture dimension** as giving the **higher angular resolution**.

---

**(b) G01.1b — Least counts**  

- Protractor least count:
  \[
  \theta_{az,\min} = \textbf{[value]}^\circ
  \]
- Digital inclinometer least count:
  \[
  \theta_{alt,\min} = \textbf{[value]}^\circ
  \]

---

**(c) G01.2 — Galactic longitude observations**  
For each listed longitude \(\ell\), record in the summary sheet:

- time of observation
- altitude
- azimuth
- \(v_{\rm corr}\)

Then point the telescope to the corresponding altitude/azimuth and save the spectrum as the appropriate \(\ell.csv\) file.

---

**(d) G01.3 — Sky and ground calibration**  

Record the following for the calibration files:

- **sky.csv**: telescope pointed to a sky region away from the Galactic plane  
  - altitude: **[value]**
  - azimuth: **[value]**
  - time: **[value]**

- **ground.csv**: telescope pointed toward the ground  
  - altitude: **[value]**
  - azimuth: **[value]**
  - time: **[value]**

---

**(e) G01.4 — Gain/temperature calibration**  
Perform the gain and temperature calibration using Tab 4.  
Use the calibrated spectra for all subsequent HI-line measurements.

---

**(f) G01.5a — Most redshifted HI frequency**  
For each Galactic longitude \(\ell\), identify the most redshifted HI line point that is \(\sim 5\,\mathrm{K}\) above the baseline and record:

\[
f_{\rm obs}(\ell)=\textbf{[value]}
\]

for each of the 5 longitudes.

---

**(g) G01.5b — Earth-frame and LSR velocities**  
Using the rest frequency \(f_0 = 1420.4058\ \mathrm{MHz}\),

\[
v_{\rm obs,Earth}(\ell)=c\,\frac{f_0-f_{\rm obs}}{f_0}.
\]

Then apply the software correction \(v_{\rm corr}\) with the lab’s sign convention to obtain

\[
v_{\rm LSR}(\ell)=v_{\rm obs,Earth}(\ell)\pm v_{\rm corr}.
\]

Record both \(v_{\rm obs,Earth}\) and \(v_{\rm LSR}\) for each longitude.

---

**(h) G01.5c — Rotation velocity and Galactic radius**  
Using the standard tangent-point/inner-Galaxy convention assumed by the lab software,

\[
R = R_0\sin\ell,
\]
and
\[
v_{\rm rot}(R)=v_{\rm LSR,max}+v_0\sin\ell,
\]
where \(R_0\) and \(v_0\) are the adopted Galactic constants.

Record for each of the 5 longitudes:

- \(R\)
- \(v_{\rm rot}(R)\)

---

**(i) G01.6 — Rotation curve**  
Plot \(v_{\rm rot}\) versus \(R\) on the graph sheet and draw a smooth curve through the points.

---

**(j) G01.6a — Enclosed mass**  
Assuming spherical symmetry,

\[
M_{\rm encl}(R)=\frac{v_{\rm rot}^2R}{G}.
\]

Express in solar masses:
\[
\frac{M_{\rm encl}}{M_\odot}
=
\frac{v_{\rm rot}^2R}{GM_\odot}.
\]

Compute this for each observed radius.

---

**(k) G01.6b — Baryonic and total mass curves**  
Plot your calculated \(M_{\rm encl}(R)\) on the same graph as the given baryonic-mass points (\(\odot\) symbols).  
Draw two smooth physically correct curves:

- baryonic mass curve
- total enclosed mass curve

---

**(l) G01.6c — Dark matter mass**  
The enclosed dark matter mass is

\[
M_{\rm dm}(R)=M_{\rm encl}(R)-M_{\rm baryon}(R).
\]

Record \(M_{\rm dm}(R)\) for each radius in the summary table.

---

**(m) G01.7 — Sensitivity per spectral bin**  
The spectrum has 512 bins across \(2.048\ \mathrm{MHz}\), so the bin width is

\[
\Delta f=\frac{2.048\ \mathrm{MHz}}{512}=4\ \mathrm{kHz}.
\]

So the **frequency resolution is \(4\ \mathrm{kHz/bin}\)**.  
The temperature sensitivity per bin cannot be determined from the binning alone without the calibrated noise level.

---

**(n) G01.8 — Effect of larger aperture**  
A horn antenna with larger aperture dimensions improves:

- **A. Sensitivity \(\sigma_T\) for \(T_{\rm ant}=5\,\mathrm{K}\)**
- **B. Angular resolution**

Do **not** tick:

- **C. Estimation of \(v_{\rm rot}\)**  
- **D. Resolution in frequency**

✅ **Correct options: A and B**

---

**Final checked answers known numerically from the problem statement:**

- **G01.7:** \(4\ \mathrm{kHz}\) per spectral bin  
- **G01.8:** **A, B**


