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
