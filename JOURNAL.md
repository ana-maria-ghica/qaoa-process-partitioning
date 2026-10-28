# Project journal

Quantum vs. classical graph partitioning for distributed process placement.
One entry per stage: what was done, what came out, what went wrong and how it was fixed.

---

## Stage 0 — First circuit on a real QPU (22 Oct 2026)

**Done.** Bell circuit (H on q0, CNOT 0→1), 1,000 shots, on the Aer simulator and on `ibm_fez`
(job `dbd7dt7i0auc7394s3lg`, 2 s of QPU time).

**Results.**
- Simulator: `00` = 479, `11` = 521, no `01`/`10`. The 50/50 split is off by 1.3σ (σ ≈ 16 at 1,000 shots): statistical noise.
- QPU: `00` = 475, `11` = 456, `01` = 35, `10` = 34, so **6.9% of the outcomes are impossible for an ideal Bell state**.
  The errors are symmetric (`01` ≈ `10`), which points to readout errors rather than a biased gate.
  The `00` > `11` asymmetry could be T1 relaxation, but at ~1σ it is not significant.

**Takeaway.** The full pipeline (circuit → transpilation → Sampler → counts) works on both targets, and a two-gate circuit
already loses a few percent to hardware noise.

---

## Stage 1 — Quantum fundamentals (23 Oct 2026)

**Done.** ⟨Z⟩ and ⟨ZZ⟩ from the Stage 0 counts; an interference experiment (H → RZ(θ) → H); the cost of every bitstring
of a triangle graph, by hand and from the diagonal of its Hamiltonian; `bitstring_to_partition`; the energy of the uniform superposition.

**Results.**
- ⟨Z₀Z₁⟩ = 1.000 on the simulator and 0.862 on the QPU, i.e. 1 − 2 × 0.069: the Stage 0 error rate shows up directly in the expectation value.
- Interference, P(0) = cos²(θ/2): exact at θ = 0 and π, 0.506 vs. 0.5 at θ = π/2 (within 1σ).
  After RZ the measurement probabilities are always ½/½; the phase alone decides the outcome after the second H.
- Triangle: cost 0 for `000` and `111`, 2 for the other six bitstrings. H = 1.5 − 0.5·(Z₀Z₁ + Z₀Z₂ + Z₁Z₂), and its diagonal matches the hand-computed table.
- Uniform superposition: ⟨H⟩ = 1.5, both by hand and with `StatevectorEstimator`.

**Why a Hamiltonian is a cost function.** Z maps a bit to ±1, so ZᵢZⱼ is +1 when two bits agree and −1 when they differ.
(1 − ZᵢZⱼ)/2 is therefore 1 for a cut edge and 0 otherwise, and summing it over the edges counts the cut edges.
The resulting matrix is diagonal, with the cost of each bitstring on the diagonal, and the energy of a state is the average cost
of the bitstrings it produces when measured.

**Observations.**
- The minimum cost (0) puts every process on one machine: mathematically optimal, useless in practice. This motivates the balance constraint (Stage 3).
- A bitstring and its complement have the same cost (machines A and B swapped): 8 bitstrings, 4 distinct partitions.
- 1.5 is the average cost of a random partition. It is both the starting point of QAOA and the random-guessing baseline of the final analysis.

---

## Stage 2 — The classical problem (24 Oct 2026)

**Done.**
- `src/graphs.py`: generators for ring, grid, 3-regular, random (edge probability 0.4) and complete graphs; 25 instances (n = 6…14), fixed seed 42, saved to `data/instances.json`.
- `src/classical.py`: `cut_value`; brute force for Max-Cut and bisection, returning all optimal solutions; greedy local search with 20 random restarts
  (node moves for Max-Cut, swaps for bisection); exact mean and standard deviation of the cost over all allowed partitions.
- `data/reference.csv`: 50 rows (25 graphs × 2 problems), the yardstick for every later result.

**Results.**
- Greedy found the optimum on **all 50 rows**: at n ≤ 14 a simple heuristic is enough.
- Complete graphs: every bisection costs (n/2)², so the standard deviation is 0 and every balanced partition is optimal (sanity check passed).
- The number of optimal solutions is always even, since every solution comes with its complement.

**Decisions.**
- Grid for n = 12: 3 × 4, the closest to square.
- The random baseline is computed exactly by enumeration, not by sampling: at n ≤ 14 enumeration is instant.

**Pitfalls.**
- Tests on symmetric graphs (ring, complete, triangle) cannot catch a bit-ordering bug; an asymmetric test graph was added.
- Initialising the minimum with a fixed number (n) fails on complete graphs, where every cut is larger; `None` is used instead.
- The random generator must be created once, outside the restart loop, otherwise every restart starts from the same point.

---

## Stage 3 — From graphs to Hamiltonians (25 Oct 2026)

**Done.** `src/hamiltonians.py`:
- `max_cut_hamiltonian`: energy = −cut (−0.5·I + 0.5·ZᵢZⱼ per edge);
- `bisection_hamiltonian`: energy = cut + A·(ΣZᵢ)² (0.5·I − 0.5·ZᵢZⱼ per edge, plus A·n·I and 2A·ZᵢZⱼ for every pair i < j);
- `generate_penalty_A`: A = (d_max + 1)/4;
- exhaustive tests over all 2ⁿ bitstrings of all 25 instances, and a check of the ground states of the bisection Hamiltonian;
- `count_zz_terms` and the table `results/hamiltonian_terms.csv`.

**Results.**
- Both Hamiltonians reproduce the classical cost on every bitstring of every instance.
- The ground states of the bisection Hamiltonian are exactly the optimal bisections from Stage 2, all balanced.
- Max-Cut needs one ZZ term per edge; bisection needs one per **pair**, n(n−1)/2, whatever the graph.
  The overhead is largest on sparse graphs (6.5× on ring_14) and 1× on complete graphs, which already have every pair as an edge.

**Experiment: how small can the penalty be?**
- ring_8 (theoretical bound 0.5): the ground state stays balanced down to A = 0.05, because an unbalanced "arc" also cuts only 2 edges and can never win.
- random_10 (bound 1.5): fails at A = 0.15, where a 6+4 split with cut 6 plus penalty 0.6 (energy 6.6) beats the optimum of 7. The real threshold is ≈ 0.25.
- The bound d_max/4 is sufficient, not necessary: a worst-case guarantee, about 6× too conservative on random_10.

**Consequences for later stages.**
- The penalty makes the bisection Hamiltonian dense: every pair of qubits interacts, so it will need far more two-qubit gates than Max-Cut (Q5).
- A is well above what is needed, so the penalty may dominate the QAOA landscape. A smaller A is a possible extension.

**Pitfalls.**
- `to_sparse_list` and `from_sparse_list` go in opposite directions.
- The penalty constant (A·n) is added once, not once per pair.
- The cut enters with opposite signs: −cut for Max-Cut (maximised), +cut for bisection (minimised).
- The exhaustive test must include unbalanced bitstrings, otherwise the penalty is never tested.
- The dense matrix does not fit in memory at 14 qubits; `to_matrix(sparse=True)` is used instead.

---

## Stage 4 — QAOA on the ideal simulator (25–26 Oct 2026)

**Done.**
- `src/qaoa.py`: `build_qaoa` (QAOAAnsatz transpiled to h, rx, rz, rzz), `hamiltonian_diagonal`, `energy` (statevector + diagonal),
  `energy_landscape`, `optimize_qaoa` (COBYLA, 10 random starts, 200 evaluations, optional warm start), `warm_start`, `all_cuts`, `qaoa_metrics`.
- 50 × 50 energy landscapes at p = 1 for ring_12 and random_12, both problems.
- Optimised angles for 25 instances × 2 problems × p = 1, 2, 3 → `results/params_warm.json`, `results/sim_ideal_warm.csv`.
- Metrics: valid_fraction, mean_cut, p_optimal, best_sample_cut (4,000 sampled shots).
- Angle transfer test: ring_8 → ring_12 and random_8 → random_12 → `results/transfer.csv`.

**Results.**
- Rings, Max-Cut: approximation ratio exactly 3/4, 5/6 and 7/8 for p = 1, 2, 3 on every size, with identical optimal angles.
- Landscapes: Max-Cut has one wide, smooth valley; bisection has narrow stripes along γ, because the large penalty coefficients make the phases oscillate quickly.
- Score S (0 = random guessing, 1 = optimal; complete graphs excluded): Max-Cut ≈ 0.45 → 0.68 → 0.80 for p = 1, 2, 3, consistent across graph types;
  bisection 0.15–0.55 with large spread, and more layers help little.
- Transfer: Max-Cut angles transfer almost perfectly (ring 100%, random 97–99%). Bisection angles do not: on ring_12 they balance far fewer partitions
  (valid_fraction 0.34–0.58 vs. 0.93), on random_12 they keep ~84% of the quality.

**Conclusions.**
- Ideal QAOA is reliable and predictable on Max-Cut, but weak and unstable on penalised bisection, even without noise.
- For bisection, the lowest energy is not what matters in practice: with a large A the optimiser favours balance over a good cut.
- Optimal angles are not unique (periodicity, symmetries), so results are compared by energy, never by angle values.

**Issues and fixes.**
- One landscape (random_10) took over 12 minutes: QAOAAnsatz simulated the cost layer as matrix exponentials.
  Transpiling to elementary gates (~70× faster) and computing the energy from the Hamiltonian diagonal (~2.5×) fixed it. Lesson: time one call before a long loop.
- The full optimisation was too slow at n = 14, p = 3; COBYLA was capped at 200 evaluations.
- **Energy increased with p** in ~17 bisection cases. A warm start (previous angles plus a new layer at angle 0, which leaves the energy unchanged) should make that impossible,
  yet ~9 violations remained. Step-by-step diagnosis: the warm start had the correct energy, and COBYLA started from it did improve,
  so the bug had to be in `optimize_qaoa`. Three leftover lines in the loop overwrote every start with a new random one, so the warm start was never used.
  After the fix: 0 violations.
- A kernel restart followed by the save cell emptied the JSON file (`open(..., "w")` truncates before writing). An assertion now checks that there is data to save.
- The transfer quality for bisection was first computed as mean_cut / optimum; for a minimisation problem it is optimum / mean_cut.
- An approximation ratio of 1.64 revealed that the bisection optimum had been used for Max-Cut. A ratio above 1 is a reliable bug signal.

**Checks that passed.** Statevector energy = Estimator to 10⁻¹⁵; 0 monotonicity violations; |mean_cut + energy| ≤ 7.5·10⁻¹³ on Max-Cut;
`qaoa_metrics` reproduces a hand-computed example.

**Limitations.** COBYLA sometimes stops at the evaluation limit (mostly bisection, p = 3); A is far above the real threshold;
for bisection, mean_cut and S ignore unbalanced shots, so the practical quality is lower than S suggests.

---

## Stage 5 — Preparing for hardware (26 Oct 2026)

**Done.**
- Compared the available QPUs by **median** calibration values and chose `ibm_boston`; saved a calibration snapshot.
- Transpiled all 100 circuits (25 graphs × 2 problems × p = 1, 2) with 5 seeds × 2 Hamiltonian term orders → `results/transpilation_ibm_boston.csv`.
- First noise-model simulation on 12 circuits → `results/stage5_noisy_ibm_boston.csv`.
- `src/hardware.py`: calibration snapshots, backend comparison, best-of-seeds transpilation, ESP, counts → probabilities.

**Hardware facts that shaped the design.**
- Native gates on Heron: rz, sx, x and cz. rz is virtual (no error, no duration), so the real cost lies in CZ gates and readout.
- CZ only between neighbours on a heavy-hex lattice (degree ≤ 3, shortest cycle 12 qubits), so non-adjacent interactions need SWAPs.
- Listing backends, reading calibrations, transpiling and simulating locally use no QPU time; only jobs that run on the processor do.

**Backend choice.**

| backend | CZ error | readout | T1 (µs) | T2 (µs) | degree | queue |
|---|---|---|---|---|---|---|
| ibm_boston | 0.119% | 0.63% | 246 | 286 | 3 | 6 |
| ibm_pittsburgh | 0.155% | 0.43% | 287 | 319 | 3 | 8 |
| ibm_kingston | 0.175% | 0.90% | 252 | 160 | 3 | 17 |
| ibm_phoenix | 0.182% | 0.68% | 176 | 158 | 4 | 2645 |
| ibm_marrakesh | 0.253% | 1.46% | 167 | 84 | 3 | 1998 |
| ibm_fez | 0.262% | 1.05% | 127 | 89 | 3 | 2 |

P(no error) ≈ (1 − e_CZ)^N_CZ × (1 − e_readout)^n. At 100 CZ gates Boston and Pittsburgh are equal (~0.81); at 200, Boston wins (0.72 vs. 0.69).
Bisection circuits are CZ-heavy, and readout errors can be partly mitigated afterwards while CZ errors cannot, so Boston was chosen.
Phoenix has better connectivity, but its queue made it impractical.

**Transpilation.**
- ring_6, Max-Cut, p = 1: 12 ideal CZ become 19, because a 6-cycle does not fit on heavy-hex and needs SWAPs. ring_12 fits exactly on a 12-qubit cycle: 24 CZ, no SWAPs.
- **The order of the Hamiltonian terms matters.** Bisection circuits with the same number of ZZ terms needed different CZ counts (n = 10: ring 166, grid 194, complete 140).
  Random angles gave the same counts, ruling out the angles. Sorting the terms (`H.sort()`) brought all three to 140, so the order drives the SABRE routing.
  The terms commute, so the circuit is mathematically identical. Every circuit is now transpiled in both orders and the version with fewer CZ gates is kept.
- After sorting, bisection costs the same on every graph of a given n. Empirical rule: **CZ ≈ 3 · p · n(n−1)/2**.
  At n = 14 that is 4–9× more CZ than Max-Cut on sparse graphs (Q5).

**Noise model (`AerSimulator.from_backend`).** It includes gate errors, T1/T2 relaxation and readout errors, but not crosstalk or calibration drift,
so the real QPU should be somewhat worse.
- Max-Cut: mean_cut drops only 1–2% even at n = 14, p = 2; p_optimal drops 18%. ESP is pessimistic for averaged metrics: an error flips one or two bits, it does not destroy the cut.
- Bisection at n = 14, p = 2: valid_fraction 0.45 → 0.37 (random guessing: 0.21), mean_cut 9% worse.
- On Max-Cut p = 2 stays better than p = 1 with noise; on bisection at n = 14 the second layer no longer helps.

**Issues and fixes.**
- Measurement time is not a selection criterion: what matters is CZ error, then readout, then T1/T2.
- Single-qubit values are not representative, and a few broken qubits distort a mean, so whole-chip medians are compared.
- The calibration snapshot came out for the wrong backend: the comparison loop reused the variable `backend` and left it pointing at the last QPU.
  The loop variable is now `candidate` and the backend is set explicitly by name.
- Calibration data can be missing (Boston: no T1 on qubit 10, no T2 on qubit 146); the snapshot handles `None` values.
- A ~40% CZ overhead on grid_10 came from an implementation detail (term order), not from the problem. Lesson: rule out the code before attributing a difference to the physics.

**QPU plan.** `data/qpu/circuit_list_2026-10-26.csv`: 36 circuits (ring, 3-regular, random × n = 6, 10, 14 × 2 problems × p = 1, 2)
plus 2 stress tests (bisection, p = 3, ~900 CZ). Predictions from ESP and ideal score: 18 "works", 9 "weak", 11 "fail".
Three circuits (ring_6 Max-Cut, regular3_10 bisection, random_14 Max-Cut, p = 1) are repeated on another day. The list is frozen before the first QPU run.

---

## Stage 6 — Runs on the QPU (27–28 Oct 2026)

**Backend change.** The pilot job sat 19 hours in the `ibm_boston` queue without starting, while the queue grew from 6 to 365 jobs.
It was cancelled and the runs moved to `ibm_pittsburgh`, practically tied with Boston in Stage 5 (worse CZ error, better readout and T1/T2) and with a queue of 7.
The circuit list stayed the same; transpilation and noise simulation were redone for Pittsburgh. Lesson: check the queue right before submitting.

**Runs.**
- Pilot: 2 circuits, 1,000 shots, 3 s of QPU time.
- Main run: 38 circuits in 3 jobs (grouped by n), 4,000 shots each, 48 s of QPU time.
- Repeat (28 Oct): the 3 selected circuits, 4,000 shots, 5 s.
- Random-guessing baseline: 4,000 uniform samples per instance (seed 1234), processed exactly like QPU counts.

**Making the runs reproducible without the IBM account.** For every job, `save_job_data` stores the transpiled circuits (`.qpy`), the raw counts (`.json`)
and one row in `data/qpu/manifest.csv` (job ID, tag, backend, shots, QPU time, calibration file). A receipt with the job IDs is written immediately after submission,
and every cell that submits jobs is blocked with `raise RuntimeError` once it has run.

**Issues and fixes.**
- The kernel died after the pilot. Results stay on IBM's servers, so the jobs were reloaded by ID and the circuits from the saved `.qpy` files.
- A later re-transpilation overwrote the file listing the submitted circuits. The manifest and the `.qpy` files proved which circuits had actually been sent, and the inconsistent file was deleted.
- The repeat job stayed "In progress" for over 20 minutes for 5 s of QPU time: on a shared instance, jobs are interleaved with other users' work.

---

## Stage 7 — Analysis (27–28 Oct 2026)

**Done.**
- `results/all.csv`: one tidy table, one row per (instance, problem, p, platform), with platforms ideal, QPU, noise model, random guessing and greedy (294 rows).
- Score S = (random_mean − mean_cut) / (random_mean − optimum) and improvement factor = P(optimum) / P_random(optimum).
- 95% bootstrap confidence intervals for every QPU circuit, the full noise-model simulation of all 38 circuits, figures F1–F7 and the day-to-day comparison.

**Key results.**
- **Q1 (ideal):** Max-Cut improves steadily with p (S ≈ 0.45 → 0.80); bisection stays at 0.15–0.55 and is unstable.
- **Q2 (hardware):** the QPU loses 0.04–0.16 in S relative to the ideal simulator. The Aer noise model explains about half of that loss (48%) and is optimistic in every case;
  ESP is pessimistic (rank correlation 0.84). The real QPU falls between the two.
- **Q3 (vs. random):** on Max-Cut the QPU samples the optimum 3–500× more often than random guessing; on bisection the gain depends on the graph (35–57× on regular3_14, none on random_14).
- **Q4 (vs. classical):** greedy finds every optimum; the best of 4,000 QPU shots finds 17 of 18, random sampling 14 of 18. At n ≤ 14 there is no quantum advantage.
- **Q5 (bisection vs. Max-Cut):** the balance constraint makes circuits 4–9× deeper, and scores far lower, on the same graph.
- Predictions: 29 of 38 correct; 7 of the 9 errors were pessimistic, consistent with ESP.
- Day-to-day variability: changes ≤ 0.02 in S, 2–8× smaller than the hardware losses. The conclusions do not depend on the day of the run.

**Issues and fixes.**
- Merging reference columns into a table that already had them produced `_x`/`_y` duplicates; the merge helper now drops old copies first.
- The first noise simulation saved only at the end and was lost when interrupted. It now saves after every circuit and resumes where it stopped.
- The first bootstrap reran the brute force on each of the 1,000 resamples. The fast version computes cuts and optima once per circuit and draws all resamples
  from a multinomial in one call: seconds instead of minutes.
- On complete graphs the score is 0/0 for bisection. Four of these cases came out as −∞ instead of NaN, because the ideal mean cut carried a rounding error of ~10⁻¹⁰;
  `score` now returns NaN whenever the denominator is (close to) zero.