## 2026-10-22 — Etapa 0: primul circuit pe QPU

**Ce am făcut:** circuit Bell (H pe q0, CNOT 0→1), 1.000 de shot-uri,
pe simulatorul Aer și pe QPU.

**Detalii rulare QPU:**
- Job ID: dbd7dt7i0auc7394s3lg
- Backend: ibm_fez
- Qubiți fizici: ...(? nu se mai stie)
- Timp QPU consumat: 2 sec

**Rezultate:**
- Simulator: 00 = 495, 11 = 505 (zero 01/10, cum era de așteptat)
- QPU: 00 = 475, 11 = 456, 01 = 35, 10 = 34 → 6,9% rezultate greșite

**Interpretare:**
- Diferența 495/505 pe simulator e zgomot statistic (σ ≈ 16 la 1.000 de shot-uri).
- Cele 6,9% de pe QPU vin cel mai probabil din erorile de citire
  (suma erorilor celor doi qubiți = ...%).
- 01 ≈ 10 → erori simetrice.
- 00 > 11 ar putea fi relaxarea T1, dar diferența (19) e ~1σ,
  deci nu pot concluziona cu 1.000 de shot-uri.

**Ce am învățat:** de ce sunt necesare shot-urile, cât de mare e
eroarea statistică, ce e transpilarea, cât de zgomotos e un QPU real.




## 2026-10-23 — Etapa 1: fundamente cuantice

### Ce am făcut
- Am calculat ⟨Z⟩ și ⟨ZZ⟩ din rezultatele circuitului Bell din Etapa 0.
- Experimentul de interferență: H → RZ(θ) → H, pentru θ = 0, π/2, π.
- Triunghiul (muchii 0–1, 0–2, 1–2): costul tuturor celor 8 bitstring-uri,
  pe hârtie și apoi din diagonala Hamiltonianului în Qiskit.
- Funcția bitstring_to_partition, cu teste.
- Energia superpoziției uniforme, cu Statevector și StatevectorEstimator.

### Rezultate
**Bell (din datele Etapei 0):**
- simulator: ⟨Z0Z1⟩ = 1.0
- QPU: ⟨Z0Z1⟩ = 0.862


**Interferență (1.000 de shot-uri, predicție P(0) = cos²(θ/2)):**
- θ = 0: 1.000 × '0' (predicție 1)
- θ = π/2: 506 × '0' (predicție 0,5; abatere < 1σ)
- θ = π: 1.000 × '1' (predicție 0)
→ după RZ probabilitățile erau ½/½ în toate cazurile; faza, invizibilă
  la măsurare, a decis complet rezultatul după al doilea H.

**Triunghi:** cost 0 pentru 000 și 111, cost 2 pentru celelalte 6.
Diagonala Hamiltonianului din Qiskit = tabelul de pe hârtie.
H simplificat = 1,5 − 0,5·Z0Z1 − 0,5·Z0Z2 − 0,5·Z1Z2

**Superpoziția uniformă:** ⟨H⟩ = 1,5 (manual și cu Estimator).

### Observații
- Costul minim (0) = toate procesele pe o mașină: optim matematic,
  dar inutil pentru sisteme → nevoie de constrângerea de echilibru (Etapa 3).
- Triunghiul nu poate avea toate cele 3 muchii tăiate (ciclu impar):
  Max-Cut maxim = 2.
- Un bitstring și complementul lui au același cost (A ↔ B):
  8 bitstring-uri, dar doar 4 împărțiri distincte.
- 1,5 = costul mediu al unei împărțiri aleatorii = punctul de plecare al
  QAOA și baseline-ul „aleatoriu” din analiza finală.

### Legătura Hamiltonian ↔ funcție de cost (în cuvintele mele)
[Rescrie tu. Schiță: Z traduce un bit în ±1; ZᵢZⱼ spune dacă doi biți
sunt egali; (1 − ZᵢZⱼ)/2 e 1 pentru o muchie tăiată și 0 altfel; suma pe
muchii = numărul de muchii tăiate. Matricea rezultată e diagonală, iar pe
diagonală e costul fiecărui bitstring. Energia unei stări = costul mediu
al bitstring-urilor pe care le dă la măsurare.]


## 2026-10-24 — Etapa 2: problema clasică

### Ce am făcut
- src/graphs.py: generatoare (inel, grilă, 3-regulat, aleatoriu, complet),
  25 de instanțe (n = 6…14) salvate în data/instances.json, cu seed fix (42).
- src/classical.py: cut_value, forță brută (Max-Cut și bisecție, toate
  soluțiile optime), greedy cu restarturi (swap-uri la bisecție, mutări de
  un nod la Max-Cut, 20 de restarturi), media și deviația standard a
  costului pe toate împărțirile permise.
- data/reference.csv: 50 de rânduri (25 de grafuri × 2 probleme).
- Histograme ale costurilor bisecțiilor pentru [instanțele alese], în figures/.

### Rezultate și observații
- Greedy a găsit optimul pe [X] din 50 de rânduri. Ratează pe [instanțe],
  pentru că [se blochează într-un optim local: niciun swap / nicio mutare
  nu mai îmbunătățește, deși optimul e altundeva].
- Grafurile complete: toate bisecțiile au același cost (n/2)², deci
  num_optima = C(n, n/2) și deviația standard 0 (test de sanitate trecut).
- Histograme: [ce ai observat; de exemplu cât de departe e optimul de medie
  și cât de rar apare, pe fiecare tip de graf].
- Numărul de soluții optime e mereu par: fiecare soluție vine cu complementul ei.

### Decizii
- Grila pentru n = 12: [2 × 6 sau 3 × 4] — [motivul].
- Baseline-ul aleatoriu calculat exact (enumerare), nu prin eșantionare,
  pentru că la n ≤ 14 enumerarea e instantanee.

### Capcane întâlnite
- Testele pe grafuri simetrice (inel, complet, triunghi) nu prind greșeala de
  ordine a biților → test suplimentar pe un graf asimetric.
- Valoarea inițială a optimului la minimizare: un număr fix (n) poate fi prea
  mic (graful complet) → None.
- Generatorul aleatoriu se creează o singură dată; altfel toate restarturile
  pornesc din același punct.



## 2026-10-25 — Etapa 3: din graf în Hamiltonian

### Ce am făcut
- src/hamiltonians.py:
  - max_cut_hamiltonian: energia = −tăietura (−0,5·I + 0,5·ZiZj pe muchie);
  - bisection_hamiltonian: energia = tăietura + A·(ΣZi)²
    (0,5·I − 0,5·ZiZj pe muchie, plus A·n·I și 2A·ZiZj pe fiecare pereche i<j);
  - generate_penalty_A: A = (d_max + 1)/4;
  - teste exhaustive (toate cele 2^n bitstring-uri, toate cele 25 de instanțe)
    și verificarea stărilor de energie minimă ale lui H_B;
  - count_zz_terms + tabelul results/hamiltonian_terms.csv.

### Rezultate
- Energiile ambilor Hamiltonieni coincid cu costul clasic pe toate
  bitstring-urile tuturor instanțelor.
- Stările de energie minimă ale lui H_B = exact bisecțiile optime din Etapa 2,
  toate echilibrate.
- Termeni ZZ: H_MC are câte unul pe muchie; H_B are n(n−1)/2 (toate perechile),
  indiferent de graf. Raportul cel mai mare: [tip de graf, valoare],
  raport 1 la [grafurile complete], pentru că [...].

### Experiment: pragul penalizării A
- ring_8 (prag teoretic 0,5): minimul rămâne echilibrat până la A = 0,05;
  o împărțire neechilibrată „arc” taie tot 2 muchii, deci nu poate câștiga.
- random_10 (prag teoretic 1,5): se strică la A = 0,15 (minim 6,6 = tăietura
  6 a unei împărțiri 6+4 + penalizarea 0,6). Pragul real ≈ 0,25.
- Pragul d_max/4 e suficient, nu necesar: garanție de cel mai rău caz,
  de ~6× prea conservatoare pe random_10.

### Concluzii pentru etapele următoare
- Penalizarea face H_B dens: toate perechile de qubiți interacționează →
  mult mai multe porți cu doi qubiți decât la Max-Cut (Î5).
- A-ul folosit e mult peste cel necesar → penalizarea poate domina peisajul
  QAOA; de testat ca extensie (A mai mic).
- h = 0 la ambii Hamiltonieni → fiecare bitstring are aceeași energie ca
  complementul lui.

### Capcane întâlnite
- to_sparse_list vs from_sparse_list (sensuri opuse).
- Constanta penalizării (A·n) se adaugă o singură dată, nu pe fiecare pereche.
- Semnele tăieturii diferă între Max-Cut (−T) și bisecție (+T).
- Testul exhaustiv al lui H_B trebuie să includă bitstring-urile
  neechilibrate, altfel penalizarea nu e testată deloc.
- Matricea completă nu încape în memorie la 14 qubiți → matrice rară
  (to_matrix(sparse=True)).





## 2026-10-25 / 26 — Etapa 4: QAOA pe simulator

### Ce am făcut
- src/qaoa.py: build_qaoa (QAOAAnsatz transpilat în h, rx, rz, rzz),
  hamiltonian_diagonal, energy (statevector + diagonală), energy_landscape,
  optimize_qaoa (COBYLA, 10 porniri aleatorii, maxiter 200, pornire caldă
  opțională), warm_start, all_cuts, qaoa_metrics.
- Hărți de peisaj p = 1 (50×50): triunghi, ring_12 și random_12,
  Max-Cut și bisecție → figures/landscape_*.png.
- Optimizare pe toate cele 25 de instanțe × 2 probleme × p = 1, 2, 3,
  cu pornire caldă → results/params_warm.json, results/sim_ideal_warm.csv.
- Metrici: valid_fraction, mean_cut, p_optimal, best_sample_cut (4.000 de shot-uri).
- Test de transfer: ring_8 → ring_12, random_8 → random_12 → results/transfer.csv.
- Grafic: scorul S vs. p → figures/quality_vs_p.png.

### Rezultate
- Triunghi, Max-Cut: optimizatorul atinge energia −2 (optimul) deja la p = 1;
  grila 10×10 găsise doar −1,97 (limitată de pasul grilei).
- Inele, Max-Cut: raport exact 3/4 (p = 1), 5/6 (p = 2), 7/8 (p = 3), pe toate
  dimensiunile; unghiurile optime sunt identice între inele.
- random_12, Max-Cut: raport 0,65 (aleatoriu) → 0,79 (p = 1) → 0,83 (p = 2).
- Hărți: Max-Cut = o vale largă și netedă; bisecție = dungi înguste pe axa γ
  (penalizarea cu coeficienți mari face fazele să oscileze rapid).
- Scor S (0 = aleatoriu, 1 = optim; fără grafurile complete):
  Max-Cut ≈ 0,45 → 0,68 → 0,80 pentru p = 1, 2, 3, consecvent pe toate tipurile;
  bisecție 0,15–0,55, bare de eroare mari (unele sub 0), p ajută puțin.
- Transfer: Max-Cut inel perfect (kept = 1,000), aleatoriu 97–99%.
  Bisecție inel (p = 2, 3): unghiurile transferate dau p_optimal de ~10× mai mare
  (0,13–0,21 vs 0,02), dar valid_fraction mult mai mică (0,34–0,58 vs 0,93).
  Bisecție aleatoriu: transfer slab (~84%).

### Concluzii
- QAOA ideal funcționează bine și predictibil pe Max-Cut, dar slab și instabil
  pe bisecția cu penalizare, chiar fără zgomot.
- La bisecție, energia minimă nu coincide cu ce contează în practică (p_optimal):
  A mare face optimizatorul să favorizeze echilibrul în dauna tăieturii.
- Unghiurile nu sunt unice (perioade, simetrii) → compar energii, nu unghiuri.

### Dificultăți și ce am învățat
- Harta random_10 dura >12 min: QAOAAnsatz simula pașii de cost ca exponențiale
  de matrici. Soluție: transpilare în porți simple (~70× mai rapid) + energia din
  diagonală (~2,5×). Lecție: măsor un apel cu %time înainte de bucle lungi.
- Bara de culori arăta 0–1: plt.colorbar se lega de scatter, nu de imagine.
  Soluție: plt.colorbar(image).
- Optimizarea completă (n = 14, bisecție, p = 3) era prea lentă → maxiter = 200.
- Prima rulare: energia creștea cu p în ~17 cazuri (bisecție) → pornire caldă
  (stratul nou cu unghiuri 0, deci energia nu poate crește).
- Și cu pornire caldă: încă ~9 încălcări. Diagnostic pas cu pas: punctul de
  pornire avea energia corectă, iar COBYLA pornit din el îmbunătățea → problema
  era în optimize_qaoa: în bucla de optimizare rămăseseră 3 rânduri vechi care
  suprascriau fiecare pornire cu una aleatorie nouă, deci pornirea caldă nu era
  folosită niciodată (și pornirile aleatorii difereau de prima rulare).
  După reparare: 0 încălcări.
- Restart de kernel + rularea celulei de salvare → fișier JSON golit (open "w"
  golește fișierul înainte de dump). Soluție: assert len(rows) > 0 înainte de open.
- all_cuts: "0" + n + "b" (int în loc de str) și listă în loc de array numpy.
- Formula de transfer: la bisecție (minimizare) calitatea e optim / mean_cut,
  nu mean_cut / optim; prima variantă inversa interpretarea.
- Raportul de aproximare a ieșit 1,64 → luasem optimul bisecției în loc de
  cel de Max-Cut din reference.csv. Raport > 1 = semnal de eroare.

### Verificări care au trecut
- energy (statevector) = Estimator, la 10⁻¹⁵.
- 0 încălcări de monotonie după reparare.
- Max-Cut: |mean_cut + energy| ≤ 7,5 · 10⁻¹³ pe toate rândurile.
- qaoa_metrics pe exemplul calculat de mână: 0,7 / 1 / 0,7 / 1.

### Limitări
- COBYLA oprit uneori de limita de 200 de evaluări (mai ales bisecție, p = 3).
- A = (d_max + 1)/4, mult peste pragul real necesar → domină energia.
- La bisecție, mean_cut și S ignoră shot-urile invalide → calitatea practică
  e mai mică decât arată S.
- Comparația „porniri aleatorii vs. pornire caldă” nu e încă exactă
  (prima rulare a folosit alte porniri aleatorii); de refăcut cu aceleași porniri.

### Idei pentru extensii
- Bisecție cu A mai mic (aproape de pragul real).
- Unghiurile transferate de pe grafuri mici ca pornire suplimentară.



## 2026-10-26 — Etapa 5: pregătirea pentru hardware

### Ce am făcut
- Listat QPU-urile disponibile: ibm_boston, ibm_fez, ibm_kingston, ibm_marrakesh,
  ibm_pittsburgh (156 qubiți, Heron), ibm_phoenix (120 qubiți, Nighthawk).
- Comparat backend-urile după medianele calibrării → ales ibm_boston.
- Snapshot de calibrare → data/qpu/calibration/ibm_boston_2026-10-26T11-48.json
- Transpilat toate circuitele (25 de grafuri × 2 probleme × p = 1, 2 = 100),
  cu 5 seed-uri × 2 ordini ale termenilor → results/transpilation_ibm_boston.csv
- Grafic CZ vs. n → figures/cz_vs_n_ibm_boston.png
- Simulare cu zgomot pe 12 circuite → results/sim_noisy_ibm_boston.csv
- src/hardware.py: get_two_qubit_gate, calibration_snapshot,
  save_calibration_snapshot, backend_summary, transpile_best,
  transpile_qaoa_best, estimated_success, counts_to_probabilities.

### Ce am învățat despre hardware
- Porți native pe Heron: rz, sx, x (1 qubit) și cz (2 qubiți). rzz → 2 CZ.
  rz e virtuală (eroare 0, durată 0) → costul real stă în CZ și în citire.
- Conectivitate: CZ doar între qubiți vecini. Heron: rețea heavy-hex,
  grad ≤ 3, cel mai mic ciclu are 12 qubiți. Phoenix: rețea pătrată, grad 4.
- T1 = timpul de relaxare (1 → 0); T2 = timpul de coerență a fazei.
  Pe Boston, median ~250 µs / ~290 µs; o poartă CZ durează zeci de ns.
- Listarea backend-urilor, calibrarea, transpilarea și simularea locală
  NU consumă timp de QPU; doar joburile rulate efectiv pe procesor.
- Instanța R2P4 e premium, cu buget comun (~800 min); ~88 min consumate,
  din care ale mele ~100 s → restul vine de la alți utilizatori ai instanței.

### Alegerea backend-ului
| backend | eroare CZ | citire | T1 (µs) | T2 (µs) | grad | coadă |
|---|---|---|---|---|---|---|
| ibm_boston | 0,119% | 0,63% | 246 | 286 | 3 | 6 |
| ibm_pittsburgh | 0,155% | 0,43% | 287 | 319 | 3 | 8 |
| ibm_kingston | 0,175% | 0,90% | 252 | 160 | 3 | 17 |
| ibm_phoenix | 0,182% | 0,68% | 176 | 158 | 4 | 2645 |
| ibm_marrakesh | 0,253% | 1,46% | 167 | 84 | 3 | 1998 |
| ibm_fez | 0,262% | 1,05% | 127 | 89 | 3 | 2 |
- Boston vs. Pittsburgh: P(fără erori) ≈ (1 − e_CZ)^N_CZ × (1 − e_citire)^n.
  La 100 CZ egale (~0,81); la 200 CZ, Boston 0,72 vs. Pittsburgh 0,69.
  Bisecția are multe CZ → Boston. Erorile de citire se pot corecta parțial
  ulterior, cele CZ nu.
- Phoenix: conectivitate mai bună, dar coada (2645) îl face impracticabil.

### Transpilare
- Test ring_6, Max-Cut, p = 1: 12 CZ ideal → 19 după transpilare (SWAP-uri:
  un inel de 6 nu încape ca ciclu pe heavy-hex); adâncime 8 → 56.
  Transpilatorul a ales o zonă bună a cipului (qubiții 119, 132–139).
- Seed-ul contează: câștigătorul variază între circuite (0–4).
- ring_12, Max-Cut: 24 CZ = 12 muchii × 2, fără SWAP-uri → se așază exact
  pe un ciclu de 12 qubiți.
- Ordinea termenilor (descoperire):
  - observat: la bisecție, același număr de termeni ZZ, dar CZ diferite
    (n = 10: inel 166, grilă 194, complet 140);
  - ipoteza 1 (unghiuri speciale): respinsă, aceleași CZ cu unghiuri aleatorii;
  - ipoteza 2 (ordinea termenilor influențează routing-ul SABRE): confirmată,
    cu H.sort() toate trei → 140 CZ;
  - circuitul e identic matematic (termenii ZZ comută) → unghiurile rămân valabile;
  - decizie: transpilez cu ambele ordini × 5 seed-uri, păstrez minimul de CZ.
- După sortare: bisecția costă la fel pe orice graf de același n, cât Max-Cut
  pe graful complet. Regulă empirică: CZ ≈ 3 · p · n(n−1)/2 (rețea de SWAP-uri).
- Î5, la n = 14: bisecția cere de 4–9× mai multe CZ decât Max-Cut pe grafuri
  rare (inel, grilă, 3-regulat), doar ~1,2–1,4× pe graful aleatoriu (dens).
  Costul bisecției depinde doar de n, nu de graf.

### Simulare cu zgomot (AerSimulator.from_backend(ibm_boston))
- Modelul include: erori de poartă, relaxare T1/T2, erori de citire.
  NU include: crosstalk, deriva calibrării → QPU probabil puțin mai prost.
- Bitul clasic i = nodul i (measure_all înainte de transpilare), deci
  rezultatele se citesc în aceeași convenție ca în tot proiectul.
- 12 circuite: ring_6, grid_10, regular3_14 × 2 probleme × p = 1, 2; 4000 shots.
- Max-Cut: mean_cut scade doar 1–2% (chiar la n = 14, p = 2); p_optimal
  −18% relativ la n = 14. ESP e pesimist pentru metrici de tip medie
  (o eroare inversează 1–2 biți, nu distruge tăietura).
- Bisecție: valid_fraction 0,45 → 0,37 la n = 14, p = 2 (aleatoriu: 0,21);
  mean_cut +9% (mai prost).
- Zgomotul împinge spre aleatoriu: la grid_10 bisecție, p_optimal crește
  (0,00014 → 0,00125), pentru că QAOA ideal era sub nivelul aleatoriu.
  0,00125 = 5 shots din 4000 → dominat de fluctuații statistice.
- Max-Cut: p = 2 rămâne mai bun și cu zgomot. Bisecție n = 14: p = 2 nu mai
  aduce nimic față de p = 1.

### Dificultăți și ce am învățat
- Am crezut că timpul de măsurare e criteriul de alegere. Greșit: măsurarea
  se face o singură dată; contează eroarea CZ, apoi citirea, apoi T1/T2.
- Valorile unui singur qubit nu sunt reprezentative (ex. marrakesh: citire
  0,2%, dar T2 = 39 µs pe qubitul 0) → compar mediane pe tot cipul.
- Mediana, nu media: câțiva qubiți stricați (eroare 1,0, T1 de câțiva µs)
  ar trage media în sus; transpilatorul oricum îi evită.
- Snapshot-ul a ieșit pentru ibm_pittsburgh în loc de ibm_boston: bucla de
  comparație folosea tot variabila `backend` și o suprascria cu ultimul QPU.
  Soluție: variabilă de buclă `candidate` + BACKEND_NAME fixat explicit.
- Calibrarea poate avea valori lipsă (Boston: t1 = None la qubitul 10,
  t2 = None la qubitul 146) → calibration_snapshot cu .get() și verificări None.
- Cale scrisă direct în funcție ("../data/...") depinde de locul de rulare →
  parametru cu valoare implicită + os.makedirs.
- rows_warm nu exista în notebook-ul 05 (fiecare notebook are kernelul lui)
  → încărcat din results/params_warm.json.
- Ordinea termenilor: ~40% CZ în plus la grid_10 dintr-un detaliu de
  implementare. Lecție: verific că diferențele nu vin din cod, înainte să
  le atribui problemei.

### Fișiere noi
- data/qpu/backend_comparison_2026-10-26.csv
- data/qpu/calibration/ibm_boston_2026-10-26T11-48.json
- results/transpilation_ibm_boston.csv
- results/sim_noisy_ibm_boston.csv
- figures/cz_vs_n_ibm_boston.png

### Lista pentru QPU
- data/qpu/circuit_list_2026-10-26.csv: 36 de circuite din matrice
  (inel, 3-regulat, aleatoriu × n = 6, 10, 14 × 2 probleme × p = 1, 2)
  + bisecție p = 3 pe regular3_14 și random_14 (teste de stres).
- Predicții: [câte works / weak / fail] + o frază de justificare per categorie.
- Repetare în altă zi: ring_6 Max-Cut, regular3_10 bisecție, random_14 Max-Cut (p = 1).
- Lista nu se mai schimbă după prima rulare pe QPU.