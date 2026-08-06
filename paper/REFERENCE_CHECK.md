# Reference verification status

Every citation in `refs.bib`, with how far it has been verified. Verification
was done programmatically against the **Crossref API** (`api.crossref.org`),
which returns the publisher's deposited metadata, on 2026-07-22.

---

## Corrections made — read this section

Nine entries carried over from the earlier draft's resource list were **wrong**,
six of them seriously (wrong authors, wrong venue, or in one case a completely
different paper). All are now corrected against Crossref. Had these been
submitted, they would have been a significant credibility problem.

| Old key | What was wrong | Corrected to |
|---|---|---|
| `millidge2023` | **Wrong authors.** Attributed to "Millidge, Beren et al."; the paper is by Arthur, Vine, Buckingham, Brosnan, Wilson & Harris | `arthur2023` |
| `bos2021` | **Wrong paper entirely.** DOI `10.1016/j.jad.2020.11.104` resolves to Squarcina et al., "Deep learning for the prediction of treatment response in depression" — not an early-warning-signals paper at all | `wichers2020` (Wichers, Smit & Snippe, *J. Person-Oriented Research* 6(1):1–15, doi `10.17505/jpor.2020.22042`) |
| `turanbirol2023` | **Wrong authors.** Attributed to "Turan Birol & Singh"; the paper is by Li, Henning & Camerer | `li2023` |
| `can2024` | **Wrong authors and wrong venue.** Attributed to "Can, Yekta Said et al." in *IEEE Rev. Biomed. Eng.*; the paper is by Cano, Cubillos, Alfaro & Romo in *Sensors* 24(24):8137 | `cano2024` |
| `kirtley2025openesm` | **Wrong authors.** Attributed to "Kirtley, Olivia J. et al."; openESM is by Siepe, Haslbeck, Kloft & Büchner, *Behavior Research Methods* 58:240 (2026) | `siepe2026` |
| `auge2025` | Wrong first name (Pauline → **Pierre**), wrong year (2025 → **2024**) | `auge2024` |
| `kiep2025` | Wrong year (2025 → **2023**), issue 6 not stated | `kiep2023` |
| `chen2025ema` | Wrong year (2025 → **2024**); volume/pages added (29:1374–1389) | `chen2024ema` |
| `smit2025` | Volume/issue/pages were missing; now 13(4):760–773 | `smit2025` (unchanged key) |

One further entry was **removed** in an earlier pass:

- `sano2019` — the earlier draft's title, volume and pages did not resolve to
  any real IEEE TAFFC record. Not cited in the manuscript. Do not reinstate
  without a DOI that resolves.

**Lesson recorded in the progress log:** a citation list inherited from notes
is not a verified bibliography. Six of nine spot-checked entries were wrong.

---

## CONFIRMED against Crossref (2026-07-22)

| Key | Verified |
|---|---|
| `arthur2023` | Arthur, Vine, Buckingham, Brosnan, Wilson, Harris. *PLOS Comput. Biol.* 19(9):e1011473, 2023 |
| `scheeren2025` | Scheeren, Nieuwenhuis, Crane, Roke, Begeer. *Autism* 29(12):3002–3013, 2025 |
| `auge2024` | Augé, Maruani, Humeau, Ellul, Cartigny, Lefebvre, Dellapiazza, Delorme. *JADD* 55(8):2788–2796, 2024 |
| `smit2025` | Smit, Helmich, Bringmann, Oldehinkel, Wichers, Snippe. *Clin. Psychol. Sci.* 13(4):760–773, 2025 |
| `wichers2020` | Wichers, Smit, Snippe. *J. Person-Oriented Res.* 6(1):1–15, 2020 |
| `li2023` | Li, Henning, Camerer. *Front. Behav. Econ.* 2:1225856, 2023 |
| `kiep2023` | Kiep, Spek, Ceulemans, Noens. *JADD* 55(6):2075–2084, 2023 |
| `chen2024ema` | Chen, Xi, Greene, Mandy. *Autism* 29:1374–1389, 2024 |
| `cano2024` | Cano, Cubillos, Alfaro, Romo. *Sensors* 24(24):8137, 2024 |
| `siepe2026` | Siepe, Haslbeck, Kloft, Büchner. *Behav. Res. Methods* 58:240, 2026 |
| `hosseini2022nurse` | Hosseini, Gottumukkala, Katragadda, Bhupatiraju, Ashkar, Borst, Cochran. *Sci. Data* 9:255, 2022 |
| `adamou2026` | Adamou, Kehagias, Antoniou. *Front. Psychiatry* 17:1787120, 2026 |

## CONFIRMED by direct retrieval (datasets downloaded this session)

| Key | Note |
|---|---|
| `schmidt2018wesad` | Downloaded from the authors' mirror linked off UCI ID 465; contents match (15 subjects, 4 conditions, E4 + RespiBAN) |
| `amin2022exam` | PhysioNet record retrieved; 10 students × 3 exams, ODC-BY v1.0 |
| `hosseini2022nurse` | Zenodo record 5514277; 15 nurses, 609 sessions |

## CANONICAL (stable bibliographic record, standard works)

`kramers1940` · `thom1975` · `zeeman1976` · `gilmore1981` · `gardiner2009` ·
`wissel1984` · `scheffer2009` · `scheffer2012` · `dakos2012` · `ditlevsen2010` ·
`boettiger2012` · `leemput2014` · `vandermaas1992` · `grasman2009` ·
`julier2004` · `hutzenthaler2012` · `boucsein2012` · `benedek2010` ·
`greco2016cvxeda` · `posadaquintero2020` · `shaffer2017` · `pellicano2012` ·
`chrysaitis2023` · `demetriou2018` · `demetriou2019` · `maclennan2022` ·
`nahumshani2018` · `eisenberg2019` · `wichers2021` · `sussmann1978` ·
`zahler1977`

These are foundational or widely-reproduced references whose details are
stable. Spot-checking a sample is still advisable before final submission, but
none is a carried-over note of uncertain provenance.

---

## Count

45 entries, 45 cited, all resolving. Verified with
`python code/experiments/check_citations.py`.
