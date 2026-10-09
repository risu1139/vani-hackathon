# Team decision: what seller data goes to the models (2026-10-09)

Source: the team lead (Rishav Kumar) in the Claude Code planning session on 2026-10-09.

## Verbatim

> real data will go only gst and other details like identification no pan others are related to business so think like elimination its identity consider u have all the information but u do not have information whom should it be matched to then u are not sharing anything

> names, address and all are ok we will share it whenever necessary like finding similar seller. but whenever necessary serbam should get those else how will we personalise it.

## Policy

1. **Never sent to the frontier model:** GST number, PAN and other government identification numbers.
2. **Shared only when a task needs them (minimum necessary):** seller name, business name, address and city. Examples: finding similar sellers, writing personalisation lines.
3. **Default context for the frontier decider:** business attributes (category, turnover band, business type, region), call history, outcomes, objections and free-text facts, keyed by an internal pseudonymous seller key. The mapping from key to seller stays on IndiaMART infrastructure.
4. **Sarvam voice agent:** gets what the call needs for personalisation, such as name, business name, city and past-call facts, in the opening line and the call plan.
