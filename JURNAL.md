## 2026-10-22 — Etapa 0: primul circuit pe QPU

**Ce am făcut:** circuit Bell (H pe q0, CNOT 0→1), 1.000 de shot-uri,
pe simulatorul Aer și pe QPU.

**Detalii rulare QPU:**
- Job ID: dbd7dt7i0auc7394s3lg
- Backend: ibm_fez
- Qubiți fizici: ...
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
- ⟨Z0⟩ = ..., ⟨Z1⟩ = ... (completează cu ce ți-a dat)
→ fiecare qubit e aleatoriu singur (⟨Z⟩ ≈ 0), dar împreună sunt corelați
  (⟨ZZ⟩ ≈ 1). Informația e în relația dintre qubiți: asta e întrețeserea.

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

### Capcane întâlnite
- Ordinea Qiskit: qubitul 0 e caracterul din dreapta, atât în bitstring-uri,
  cât și în etichetele SparsePauliOp ('ZIIZ' = Z0Z3).
- Testele trebuie făcute pe bitstring-uri asimetrice: un palindrom
  ('0110') nu prinde greșeala de ordine.
- Construiesc Hamiltonianul cu from_sparse_list (indici expliciți),
  nu cu etichete scrise de mână.

### Note tehnice
- qiskit_ibm_runtime.executor_sampler.Sampler funcționează și cu
  AerSimulator → folosesc primitivul nou peste tot.
- Estimator primește (circuit fără măsurare, observabilă) și întoarce ⟨H⟩;
  Sampler primește circuit cu măsurare și întoarce bitstring-uri.

### Întrebări deschise
- [ce nu ți-e încă clar; dacă nu e nimic, șterge secțiunea]
