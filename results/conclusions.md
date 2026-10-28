## Predicții vs. rezultate

| Predicție (când) | Rezultat | Confirmat? | De ce |
|---|---|---|---|
| Î1: calitatea crește cu p; mai bine pe grafuri regulate (plan) | Max-Cut: S 0,45 → 0,80 pentru p = 1 → 3, aproape identic pe toate tipurile; bisecție: S 0,15–0,55, p ajută puțin | Parțial | Creșterea cu p, da (Max-Cut); tipul grafului contează doar la bisecție; penalizarea strică optimizarea |
| Î2: pierderea pe QPU crește cu n (plan) | Max-Cut p = 2: pierdere 0,10 → 0,16; bisecție: ~0,05 constant | Parțial | Pierderea depinde mai mult de numărul de CZ (p) decât de n; la bisecție nu mai e ce pierde |
| Î3: QPU bate aleatoriul la grafuri mici, nu la cele mari (plan) | Max-Cut: bate aleatoriul la toate n (factor până la ~500); bisecție: inel și aleatoriu ajung la ghicit la n = 14, 3-regulat nu | Parțial | Factorul crește cu n pentru că ghicitul scade ∝ 1/2ⁿ; la bisecție contează graful |
| Î4: clasicul găsește optimul, QAOA rămâne în urmă (plan) | Greedy: optimul pe 50/50; QAOA departe de optim ca medie | Da | La n ≤ 14, spațiul de căutare e trivial clasic |
| Î5: bisecția are circuite mult mai adânci și rezultate mai slabe (plan) | 584 CZ vs. 65–467 la n = 14, p = 2; scor QPU mult mai mic | Da, cu nuanțe | Costul depinde doar de n; o mare parte din pierdere e deja pe ideal |
| Transfer inel, Max-Cut: kept ≈ 1 (Etapa 4) | kept = 1,000 | Da | Vecinătăți identice pe inele |
| Transfer aleatoriu, bisecție: cel mai slab (Etapa 4) | ~84% la p = 2, 3 | Da | Peisaj accidentat, alt A |
| Transfer inel, bisecție: 0,9–1,0 (Etapa 4) | Unghiurile transferate au dat p_optimal de ~10× mai mare | Nu (surpriză) | Optimizarea directă se blocase într-un minim local |
| ESP prezice rezultatul pe QPU (Etapa 5) | Corelație ~0,8, dar ESP pesimist (păstrat 57–67% la ESP 0,37) | Parțial | O eroare inversează 1–2 biți, nu distruge soluția |
| Teste de stres p = 3 vor eșua (Etapa 5) | valid_fraction 0,25–0,34 (ghicit: 0,21); optimul aproape niciodată | Da | 906 CZ, ESP ≈ 0,22 |
| [predicțiile tale works/weak/fail] | [X din 38 corecte] | | [din crosstab] |
