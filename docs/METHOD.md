# Method notes

Formulas are standard search theory; framing, worked examples and the cueing model are original synthesis. Sweep widths in every example are assumptions chosen for teaching, not measured values for any sensor.

## 01 Two different problems

Wide-area search finds sparse candidates across a large area. Narrow identification characterises a candidate whose position is already known. For a fixed detector the two trade through the field of view: the magnification that makes identification possible narrows the ground footprint, and with it the area covered per hour.

```
footprint width   w = 2R·tan(FOV/2)
area rate         Ȧ = W·v
```

A gimbal zoomed to 2° at 5 km slant range has a 175 m (0.094 NM) footprint. Staring from a platform at 80 kt it covers 7.5 NM²/h. Scanned back and forth by an operator to an effective sweep width of 2 NM, it covers 160 NM²/h, at the cost of constant attention. Buying an identification sensor for a search mission is a common and expensive error.

## 02 Sweep width

Effective sweep width W is the width of an imaginary strip in which a sensor would detect every target and outside which it would detect none, such that it finds as many targets as the real sensor with its gradual fall-off. It is defined for a stated sensor, target, altitude, visibility and sea state. Search and rescue manuals tabulate it by condition for exactly that reason. Change the target or the weather and W changes; every POD below changes with it.

## 03 Coverage and probability of detection

```
coverage factor   C = W·L / A          (L = v·t, track length in the area)
random search     POD = 1 − exp(−C)            Koopman
parallel sweep    POD ≈ erf(√π·C / 2)          inverse-cube detection law
exhaustive        POD = min(1, C)              definite-range ideal
effort needed     L = −ln(1 − POD)·A / W
```

Worked example (tested): 2,000 NM² box, W = 4 NM, 80 kt, 4 hours on task. L = 320 NM, C = 0.64. Random search gives POD 0.47; a well-flown parallel sweep gives 0.58. For POD 0.9 under random search, L = 2.303 × 2,000 / 4 = 1,151 NM, or **14.4 hours**. A scanned gimbal with W = 2 NM needs 28.8 hours. An assumed wide-area layer at 3,000 NM²/h would need 1.5 hours, and whether that holds rests entirely on whether its sweep width holds for this target and sea state.

Random search is the planning curve because real tracks overlap, navigate imperfectly and meet targets that move. Diminishing returns are built in: each extra hour finds a smaller share of what is left.

POD is conditional on the target being in the box. Multiply by the probability of area (the chance it is there at all) to get probability of success.

## 04 Cross-cueing

A cue is a geolocated detection with uncertainty. The cued sensor must slew, settle, search the uncertainty area with its own footprint, acquire and hold. The package's first-order model:

```
error radius   r = position error + target speed × cue age
cue time       t = slew/slew rate + settle + [−ln(1 − POD)·πr² / (w·u)]   (search term is 0 if w ≥ 2r)
```

Worked example: a radar cue with 150 m error, 10 s old, on a 10 m/s boat gives a 250 m radius. A 175 m footprint scanned at 100 m/s over the ground takes 25.9 s to search it to POD 0.9, against 2 s of slew and 1.5 s of settle. Cue quality (error, age) dominates slew rate. This is a model by the author, meant to show which term matters; it is not a gimbal performance model.

## 05 Track persistence and re-search time

```
r = v_max·t_gap        A_u = πr²        t_reacq ≈ −ln(1 − POD)·A_u / (W·v_g)
```

A 20 kt boat lost for 15 minutes can be anywhere within 5 NM, 78.5 NM². Re-searching with W = 2 NM at 80 kt to POD 0.9 takes 1.13 h. Lost for 30 minutes: 314 NM² and 4.5 h. Doubling the gap quadruples the re-search. `max_affordable_gap` inverts this: given one hour of re-search, the longest gap you can recover from is about 14 minutes. Preventing gaps (endurance, overlapping on-station periods, a wide-area layer that keeps tracking while the gimbal identifies) is far cheaper than recovering from them. Identity must persist too: reacquiring a boat is not reacquiring the boat unless attributes travel with the track.

## 06 Operator false-alarm burden

```
N_FA = N_c·Pfa     N_TP = N_t·Pd     PPV = N_TP / (N_TP + N_FA)     T_review = (N_TP + N_FA)·t_r
```

Worked example: 50,000 candidate objects per hour (whitecaps, debris, birds), Pfa 0.001, two real boats at Pd 0.8. That is 50 false and 1.6 true alerts, PPV 0.031, and 1,032 s of review per hour at 20 s each: 17 minutes of every hour confirming noise. A tenfold Pfa improvement gives 5 false alerts, PPV 0.24 and 132 s of review. The detector did not see better; it became usable. When alerts outrun attention, operators raise thresholds or stop responding, and effective Pd falls below the tested value.

## 07 A comparison aid, not a metric

```
V ≈ Ȧ · Pd · Q_ID / B
```

Q_ID is the probability a detection can be carried to an actionable identification; B is operator burden in operator-equivalents. With assumed inputs: gimbal only 97, wide-area only 1,080, search plus cued gimbal 2,314. The pair wins because the cue turns coverage into identification without a second full-time operator. Use it only to rank architectures under identical assumptions, never to quote a value.

## 08 Where the next investment should go

- Targets missed entirely (low POD in review)? Invest in the search layer: sweep width, area rate, endurance. Not zoom.
- Detections arrive but are not identified in time? Fix the cue: automation, position accuracy, latency.
- Operators overwhelmed? Reduce false alerts before adding sensors.
- Identified targets lost before a responder arrives? Invest in persistence and in the link to the responder.
