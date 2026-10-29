# Résultats des requêtes d'analyse (généré, ne pas éditer)

## [01_monthly_revenue](../sql/queries/01_monthly_revenue.sql)

(Direction) : comment évoluent le chiffre d'affaires et le volume de commandes mois par mois ?

| month      |   orders |   revenue |   revenue_growth_pct |
|:-----------|---------:|----------:|---------------------:|
| 2016-09-01 |        2 |    279.69 |                nan   |
| 2016-10-01 |      290 |  51354.5  |              18261.2 |
| 2016-12-01 |        1 |     19.62 |               -100   |
| 2017-01-01 |      787 | 136943    |             697879   |
| 2017-02-01 |     1718 | 283562    |                107.1 |
| 2017-03-01 |     2617 | 425618    |                 50.1 |
| 2017-04-01 |     2377 | 405849    |                 -4.6 |
| 2017-05-01 |     3640 | 582711    |                 43.6 |
| 2017-06-01 |     3205 | 499652    |                -14.3 |
| 2017-07-01 |     3946 | 578754    |                 15.8 |

_24 ligne(s) au total._

## [02_top_categories](../sql/queries/02_top_categories.sql)

(Marketing) : quelles catégories de produits génèrent le plus de chiffre d'affaires, et avec quel panier moyen ?

| category              |   orders |          revenue |   avg_item_price |
|:----------------------|---------:|-----------------:|-----------------:|
| health_beauty         |     8800 |      1.2557e+06  |           130.34 |
| watches_gifts         |     5604 |      1.19819e+06 |           200.7  |
| bed_bath_table        |     9399 |      1.03596e+06 |            93.36 |
| sports_leisure        |     7673 | 979741           |           114.06 |
| computers_accessories |     6654 | 904322           |           116.22 |
| furniture_decor       |     6425 | 727465           |            87.67 |
| housewares            |     5847 | 626826           |            90.65 |
| cool_stuff            |     3616 | 620770           |           164.27 |
| auto                  |     3872 | 586586           |           139.53 |
| garden_tools          |     3505 | 481010           |           111.14 |

_10 ligne(s) au total._

## [03_late_rate_by_state](../sql/queries/03_late_rate_by_state.sql)

(Logistique) : dans quels États les livraisons sont-elles le plus souvent en retard, et combien de jours faut-il pour livrer ?

| customer_state   |   delivered_orders |   late_rate_pct |   avg_delivery_days |
|:-----------------|-------------------:|----------------:|--------------------:|
| AL               |                397 |            21.4 |                24.5 |
| MA               |                717 |            17.4 |                21.5 |
| SE               |                335 |            15.2 |                21.5 |
| PI               |                476 |            13.9 |                19.4 |
| CE               |               1279 |            13.8 |                21.2 |
| BA               |               3256 |            12.2 |                19.3 |
| RR               |                 41 |            12.2 |                29.3 |
| RJ               |              12350 |            12.1 |                15.2 |
| PA               |                946 |            11.2 |                23.7 |
| ES               |               1995 |            10.7 |                15.7 |

_27 ligne(s) au total._

## [04_review_score_vs_delay](../sql/queries/04_review_score_vs_delay.sql)

(Service client) : un retard de livraison dégrade-t-il la note laissée par le client ?

| delay_bucket       |   reviews |   avg_score |   negative_rate_pct |
|:-------------------|----------:|------------:|--------------------:|
| 0. à l'heure       |     89944 |        4.29 |                 9.3 |
| 1. 1-3 jours       |      1856 |        3.29 |                32.2 |
| 2. 4-7 jours       |      1756 |        2.1  |                67.7 |
| 3. plus de 7 jours |      2797 |        1.7  |                79.2 |

_4 ligne(s) au total._

## [05_repeat_purchase_rate](../sql/queries/05_repeat_purchase_rate.sql)

(Marketing) : quelle part des clients revient acheter ?

|   customers |   repeat_customers |   repeat_rate_pct |   avg_orders_per_customer |
|------------:|-------------------:|------------------:|--------------------------:|
|       94990 |               2888 |              3.04 |                     1.034 |

_1 ligne(s) au total._

## [06_seller_pareto](../sql/queries/06_seller_pareto.sql)

(Direction) : le chiffre d'affaires est-il concentré sur quelques vendeurs (loi de Pareto) ?

|   seller_rank | seller_id                        | seller_state   |   revenue |   cumulative_share_pct |
|--------------:|:---------------------------------|:---------------|----------:|-----------------------:|
|             1 | 4869f7a5dfa277a7dca6462dcf3b52b2 | SP             |    229238 |                    1.7 |
|             2 | 53243585a1d6dc2643021fd1853d8905 | BA             |    222776 |                    3.3 |
|             3 | 4a3ca9315b744ce9f8e9374361493884 | SP             |    200326 |                    4.8 |
|             4 | fa1c13f2614d7b5c4749cbc52fecda94 | SP             |    192842 |                    6.3 |
|             5 | 7c67e1448b00f6e969d365cea6b010ab | SP             |    187924 |                    7.7 |
|             6 | 7e93a43ef30c4f03f38b393420bc753a | SP             |    172584 |                    8.9 |
|             7 | da8622b14eb17ae2831f4ac5b9dab84a | SP             |    160237 |                   10.1 |
|             8 | 7a67c85e85bb2ce8582c35f2203ad736 | SP             |    141716 |                   11.2 |
|             9 | 1025f0e2d44d7041d6cf58b6550e0bfa | SP             |    138969 |                   12.2 |
|            10 | 955fee9216a65b617aa5c0531780ce60 | SP             |    135160 |                   13.2 |

_50 ligne(s) au total._

## [07_payment_mix](../sql/queries/07_payment_mix.sql)

(Finance) : comment les clients paient-ils, et en combien de mensualités ?

| payment_type   |   payments |   share_pct |   avg_value |   avg_installments |
|:---------------|-----------:|------------:|------------:|-------------------:|
| credit_card    |      76795 |        73.9 |      163.32 |                3.5 |
| boleto         |      19784 |        19   |      145.03 |                1   |
| voucher        |       5775 |         5.6 |       65.7  |                1   |
| debit_card     |       1529 |         1.5 |      142.57 |                1   |
| not_defined    |          3 |         0   |        0    |                1   |

_5 ligne(s) au total._

## [08_rfm_scores](../sql/queries/08_rfm_scores.sql)

(Marketing) : base de la segmentation RFM, avec pour chaque client sa récence, sa fréquence, son montant et un score de 1 à 5.

| customer_unique_id               |   recency_days |   frequency |   monetary |   r_score |   f_score |   m_score |
|:---------------------------------|---------------:|------------:|-----------:|----------:|----------:|----------:|
| 0a0a92112bd4c708ca5fde585afaa872 |            384 |           1 |   13664.1  |         2 |         5 |         5 |
| da122df9eeddfedc1dc1f5349a1a690c |            565 |           2 |    7571.63 |         1 |         5 |         5 |
| 763c8b1c9c68a0229c42c9fc6f662b93 |             95 |           1 |    7274.88 |         5 |         5 |         5 |
| dc4802a71eae9be1dd28f5d788ceb526 |            613 |           1 |    6929.31 |         1 |         5 |         5 |
| 459bef486812aa25204be022145caa62 |             85 |           1 |    6922.21 |         5 |         5 |         5 |
| ff4159b92c40ebe40454e3e6a7c35ed6 |            512 |           1 |    6726.66 |         1 |         5 |         5 |
| 4007669dec559734d6f53e029e360987 |            328 |           1 |    6081.54 |         2 |         5 |         5 |
| eebb5dda148d3893cdaf5b5ca3040ccb |            548 |           1 |    4764.34 |         1 |         5 |         5 |
| 48e1ac109decbb87765a3eade6854098 |            118 |           1 |    4681.78 |         5 |         5 |         5 |
| c8460e4251689ba205045f3ea17884a1 |             71 |           4 |    4655.91 |         5 |         5 |         5 |

_94989 ligne(s) au total._
