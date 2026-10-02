# Modèle financier

Le tableur [`modele-financier.xlsx`](modele-financier.xlsx) contient tout le calcul (252 formules). Il s'ouvre dans Excel, LibreOffice ou Google Sheets. **Ne modifiez que les cellules en bleu** : les résultats se recalculent.

| Onglet | À quoi il sert |
|---|---|
| **Hypothèses** | Toutes les données d'entrée : écoles, élèves, prix, charges, coût d'acquisition, attrition, capital. Chaque ligne indique sa source ou sa justification. |
| **Projection 3 ans** | Le chiffre d'affaires, les charges, le résultat et le revenu annuel récurrent. |
| **Trésorerie An 1** | Le mois par mois de la première année et le besoin de financement de départ. |
| **Économie unitaire** | Ce qu'une école rapporte et coûte : marge, délai de remboursement, LTV, LTV/CAC. |
| **ROI école** | Le calcul à remplir devant un fondateur pendant le rendez-vous. |

---

## Résultats du scénario de base (FCFA)

| | An 1 | An 2 | An 3 |
|---|---:|---:|---:|
| Écoles en fin d'année | 40 | 180 | 500 |
| Écoles actives en moyenne | 24 | 110 | 340 |
| Revenu moyen par école (ARPA) | 300 000 | 320 000 | 350 000 |
| Chiffre d'affaires | 7 675 000 | 38 700 000 | 127 000 000 |
| Total des charges | 5 035 000 | 30 305 000 | 85 840 000 |
| **Résultat avant impôt** | **2 640 000** | **8 395 000** | **41 160 000** |
| Marge | 34 % | 22 % | 32 % |
| **Revenu annuel récurrent en fin d'année** | 12 000 000 | 57 600 000 | **175 000 000** |

L'an 2 est moins rentable que l'an 1 : c'est l'année où l'on recrute (commerciaux, support, développeur) et où l'on ouvre un deuxième pays. C'est un investissement voulu, qui prépare la croissance de l'an 3.

## Trésorerie de l'an 1

- **Point bas** : environ **−373 000 FCFA** en novembre (cumul des flux sans capital). Les pilotes sont gratuits en octobre et novembre.
- La trésorerie redevient positive en **février 2027**.
- Avec **1 million de FCFA** de capital, la trésorerie ne descend jamais sous 600 000 FCFA.
- Le calcul est prudent : les revenus sont lissés sur 12 mois, alors qu'en réalité les écoles paient leur abonnement en 3 tranches, souvent à l'avance.

## Économie unitaire

| Indicateur | Valeur (An 1) | Repère |
|---|---:|---|
| Marge brute par école | 260 000 FCFA par an (87 %) | Un logiciel coûte peu à servir |
| Coût d'acquisition (CAC) | 80 000 FCFA | Commission et terrain |
| Délai de remboursement du CAC | 3,7 mois | Excellent : moins de 12 mois |
| LTV (durée de vie plafonnée à 5 ans) | 1 300 000 FCFA | |
| **LTV / CAC** | **16x** | Un modèle sain dépasse 3x |

---

## Les leviers qui changent tout (sensibilité sur l'An 3)

Chaque ligne modifie **une seule** hypothèse. Les charges restent celles du scénario de base.

| Si… | CA An 3 | Résultat An 3 | Revenu récurrent fin An 3 |
|---|---:|---:|---:|
| **Scénario de base** | 127 M | **41 M** | 175 M |
| Les écoles ont 250 élèves au lieu de 350 | 102 M | 18 M | 138 M |
| Seulement 20 % des écoles prennent Recouvrement+ | 109 M | 25 M | 149 M |
| 80 % des écoles prennent Recouvrement+ | 145 M | 57 M | 201 M |
| 300 écoles en fin d'An 3 au lieu de 500 | 87 M | 5 M | 105 M |
| 700 écoles en fin d'An 3 au lieu de 500 | 167 M | 77 M | 245 M |

**Ce qu'il faut en retenir :**
1. **Le nombre d'écoles est le levier n° 1.** Il dépend de la force de vente : recrute et forme des commerciaux dès que la méthode fonctionne.
2. **La taille des écoles compte.** Cible en priorité les écoles de plus de 300 élèves.
3. **L'offre premium fait la marge.** Chaque point de recouvrement gagné par une école cliente est l'argument qui la fait passer à Recouvrement+.
4. **Si les ventes sont en retard sur le plan, retarde les embauches**, et non l'inverse. Les charges de l'an 2 et de l'an 3 ne se justifient que si les écoles signent.

---

## Comment s'en servir chaque mois

1. Remplace les hypothèses par **tes chiffres réels** : écoles signées, taille moyenne, part de Recouvrement+, charges.
2. Compare-les au plan. Si l'écart dépasse 20 %, ajuste les recrutements.
3. Avant tout rendez-vous avec une banque, un investisseur ou un concours, mets le fichier à jour : les financeurs aiment les fondateurs qui connaissent leurs chiffres.
