# Team decision: show the seller one best-suited buy lead, money first (2026-10-10)

Source: the user, in the planning session on 2026-10-10, answering "board item 6, live / expired".

## Verbatim
> we also find one of the best suited bylead in that category it could be expired or live to attract him so the idea is tell how the company can earn from indiamart then only they willl be interested in us if we have something about money we should say about it.

## Rule
1. Board item 6 ("BL – live / expired – high value") means: find **one best-suited buy lead in the seller's category**. It can be live or expired. VANI uses it to show the seller how they can earn from IndiaMART.
2. **Money first:** if we have a money fact (an order value or a quantity), VANI should say it. Sellers become interested only when they see what they can earn.
3. Buyer identity is never said: no buyer name, company or phone. VANI may say the product, the quantity, the order value, the buyer city or region, and whether the lead is live or was recent.

## Feasibility check (same session)
pg-imblr (Redash ds 16), joining `eto_ofr` (live leads by `fk_glcat_mcat_id`, indexed) to `eto_attribute` ("Probable Order Value", "Quantity") by display id. It returns each lead's title, quantity, order value, city id and expiry in about 3 s per category. Example, MCAT 138962: "200 pcs, Rs 10,000–11,000, expires 12 Oct". Expired leads: `eto_ofr_expired` (same keys). Order values are the buyer's estimated range, not an invoice.
