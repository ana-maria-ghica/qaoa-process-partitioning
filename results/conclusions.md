# Conclusions

Results of `07_analysis.ipynb`. All QPU numbers come from `ibm_pittsburgh` (27–28 Oct 2026), 4,000 shots per circuit;
intervals are 95% bootstrap confidence intervals over the shots.

**Score S** = (random_mean − mean_cut) / (random_mean − optimum): 0 = no better than random guessing, 1 = always optimal, negative = worse than random.
**Improvement factor** = P(sampling an optimal solution) / P(random guessing samples one).

---

## Summary

- On the ideal simulator, QAOA solves **Max-Cut** well and predictably (S ≈ 0.45 at p = 1 → 0.80 at p = 3).
  **Minimum bisection**, the actual placement problem, is much harder even without noise (S = 0.15–0.55), because the balance constraint
  must be added as a penalty term.
- On real hardware, QAOA keeps a clear, statistically robust signal on Max-Cut up to 14 qubits: it samples the optimum up to ~500× more often than random guessing.
  On bisection the signal fades to random level at 14 qubits on two of three graphs.
- The penalty term, not the graph, is what makes bisection expensive: it couples every pair of qubits, so circuits need 4–9× more CZ gates on sparse graphs.
- Two pre-run predictors bracket the real result: a calibration-based noise model is optimistic (it explains about half of the hardware loss),
  ESP is pessimistic but ranks circuits correctly (correlation 0.84).
- At n ≤ 14 a classical greedy heuristic finds every optimum. The experiment measures how QAOA behaves and degrades on hardware; it does not show a quantum advantage.

---

## Q1 — Without noise, how close does QAOA get to the optimum? (F1)

| | p = 1 | p = 2 | p = 3 |
|---|---|---|---|
| Max-Cut (mean over graph types) | ≈ 0.45 | ≈ 0.68 | ≈ 0.80 |
| Bisection (range over graph types) | 0.16–0.41 | 0.19–0.50 | 0.26–0.56 |

Max-Cut improves with every layer on every graph type, with little spread between sizes. Bisection scores are lower, vary strongly with the instance,
and do not always improve with p (regular3: 0.50 → 0.48), even though the energy itself never increases with p.
The reason is the penalty: the optimiser can lower the energy by balancing more partitions without cutting fewer edges.

Supporting evidence from `04_qaoa_simulator`: Max-Cut angles transfer from 8- to 12-node graphs with no loss on rings and a 1–3% loss on random graphs;
bisection angles do not transfer reliably.

---

## Q2 — How much survives on real hardware, and does a noise model predict it? (F2, F7)

The QPU loses 0.04–0.09 in S at p = 1 and 0.05–0.16 at p = 2 relative to the ideal simulator.
On Max-Cut the second layer is still worth its extra noise (n = 14: S = 0.50 at p = 2 vs. 0.28 at p = 1); on bisection it is not.

| | ideal → QPU loss (sum over 12 groups) | explained by the Aer noise model |
|---|---|---|
| all problems, p, n | 0.95 | 0.46 (48%; 27–71% per group) |

The unexplained part is positive in every group: the noise model, built from gate, readout and T1/T2 data, is systematically optimistic,
because it ignores crosstalk, calibration drift and coherent errors. ESP (the probability that no gate fails) is the opposite: almost every circuit
keeps more of its ideal score than ESP predicts. ESP still ranks circuits correctly (correlation 0.84 over 28 circuits), so it tells which circuits
will suffer most, but not by how much. **The real QPU falls between the two predictions.**

---

## Q3 — Does QAOA on the QPU find the optimal partition more often than random guessing? (F3)

- **Max-Cut:** yes, on every instance. The improvement factor ranges from ~3 to ~500× and grows with n, because random guessing becomes hopeless faster than QAOA does.
- **Bisection:** depends on the graph. 35–57× on regular3_14, 2–5× on ring_14, and random_14 never sampled the optimum.

**Which conclusions survive the bootstrap:**
- At n = 14, bisection beats random guessing clearly only on regular3_14 (S ≈ 0.28 at p = 1 and 2).
  random_14 is barely above random at p = 1 (S = 0.10 [0.08, 0.11]) and indistinguishable from it at p = 2 (S = −0.01 [−0.03, 0.00]);
  ring_14 is statistically above random but practically negligible (S ≤ 0.035).
- The two p = 3 stress tests (~900 CZ gates) sit at random level, as predicted.
- On random_10 Max-Cut, the gain from p = 1 to p = 2 is not significant on the QPU (ΔS = 0.014 [−0.002, 0.030]): the ideal improvement is absorbed by the extra noise.

---

## Q4 — How does QAOA compare with classical methods? (F4)

| method | optimum found (18 instance/problem pairs) |
|---|---|
| greedy local search, 20 restarts | 18 |
| QAOA on the QPU, p = 2, best of 4,000 shots | 17 |
| random guessing, best of 4,000 samples | 14 |

On average, QAOA on the QPU lies between random guessing and the ideal simulator. Taking the best sample, it beats random sampling
(e.g. ring_14 and random_14 Max-Cut, regular3_14 bisection) but not greedy. At these sizes the problem is easy for a classical heuristic.

---

## Q5 — How much harder is bisection than Max-Cut on the same graph? (F5)

After transpilation, bisection needs ≈ 3 · p · n(n−1)/2 CZ gates whatever the graph, because the penalty couples every pair of qubits.
On sparse graphs at n = 14 that is 4–9× more CZ gates than Max-Cut on the same graph, and the QPU score is correspondingly far lower.
Finding a cheaper way to impose balance (a smaller penalty, or a constraint-preserving mixer) matters more than the choice of graph.

---

## Day-to-day variability

The same three circuits (n = 6, 10, 14) were run again one day later.

| circuit | S, 27 Oct | S, 28 Oct | change |
|---|---|---|---|
| ring_6, Max-Cut, p = 1 | 0.447 [0.436, 0.457] | 0.467 [0.456, 0.477] | +0.020 (just significant) |
| regular3_10, bisection, p = 1 | 0.348 [0.330, 0.365] | 0.353 [0.336, 0.368] | +0.005 |
| random_14, Max-Cut, p = 1 | 0.043 [0.033, 0.052] | 0.036 [0.027, 0.046] | −0.007 |

Day-to-day changes (≤ 0.02) are 2–8× smaller than the ideal-to-QPU losses, so the conclusions do not depend on the day of the run.

---

## Predictions made before running

Each circuit was labelled from its ESP and ideal score before submission (Stage 5).

| predicted \ observed | fail | weak | works |
|---|---|---|---|
| **fail** | 7 | 4 | 0 |
| **weak** | 0 | 6 | 3 |
| **works** | 0 | 2 | 16 |

29 of 38 predictions were correct. 7 of the 9 errors were pessimistic (mostly bisection circuits predicted to fail that reached a weak score),
consistent with ESP underestimating the hardware.

---

## Limitations

- **Small problems:** n ≤ 14 and p ≤ 3, where brute force and greedy are exact or nearly so.
- **One backend, two days:** results are specific to `ibm_pittsburgh`; the variability check covers only three circuits.
- **Angles optimised on the ideal simulator** and run unchanged on hardware; noise-aware optimisation could recover part of the loss.
- **Conservative penalty:** A = (d_max + 1)/4 is up to ~6× above the value actually needed, which likely makes bisection harder than necessary.
- **Optimiser budget:** COBYLA was capped at 200 evaluations; a few runs stopped at the limit (e.g. random_14 Max-Cut at p = 1).
- **Bisection metrics** count only balanced shots, so the practical quality is lower than S suggests when valid_fraction is low.
- **No error mitigation** was applied; readout mitigation alone would likely raise all QPU scores.
- Eight significance checks were run at once; a borderline result (ring_14, p = 1) could be a chance finding.

## Next steps

- Bisection with a smaller penalty, close to the empirical threshold, or with a mixer that preserves balance (XY mixer), avoiding the penalty altogether.
- Readout error mitigation, and angles optimised with the noise model in the loop.
- Larger instances (n = 20–30), where brute force becomes impractical and the comparison with greedy becomes meaningful.