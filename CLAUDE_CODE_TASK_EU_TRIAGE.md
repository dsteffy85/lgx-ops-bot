# Task: Add EU/UK/AU Fulfillment Triage to LGX-OPS-BOT

## Context
Starting Monday, #hardwaredeliveryhelp will receive EU/UK/AU fulfillment issues that currently go to #eu-uk-fulfillment. LGX-OPS-BOT already handles US order triage in #hardwaredeliveryhelp. We need to extend it to handle EU/UK/AU tickets using the same pattern but with region-specific logic.

## What exists today
- `scripts/slack_listener.py` — the main bot
- Bot already triages US orders in #hardwaredeliveryhelp using a playbook + Snowflake data
- Order numbers are detected by `find_order_number()` which looks for `US-XXXXXXXXX` patterns
- Triage uses `_generate_playbook_response()` which sends ticket text + order data to LLM with a playbook system prompt
- The playbook is loaded from `shared/playbook.md`

## What needs to change

### 1. Detect EU/UK/AU order numbers
Update `find_order_number()` to also detect:
- `GB-XXXXXXXXX` (UK orders)
- `IE-XXXXXXXXX` (Ireland)
- `FR-XXXXXXXXX` (France)
- `ES-XXXXXXXXX` (Spain)
- `AU-XXXXXXXXX` (Australia)
- `NZ-XXXXXXXXX` (New Zealand)
- `SG-XXXXXXXXX` (Singapore)

Pattern: `[A-Z]{2}-\d{6,9}` (2-letter country prefix + dash + 6-9 digits)

The existing `US-` pattern should still work. Just broaden the regex.

### 2. Add EU/UK/AU FAQ as triage context
Create a new file: `shared/eu_uk_au_faq.md`

This file should contain the full FAQ document content (provided below). The bot should load it at startup alongside the existing playbook.

When triaging an EU/UK/AU order (detected by prefix), inject this FAQ into the LLM system prompt in addition to the regular playbook.

### 3. Update triage system prompt for EU/UK/AU
When the order prefix is GB/IE/FR/ES/AU/NZ/SG, the triage prompt should include:
- The EU/UK/AU FAQ (shipping SLAs, carrier info, return flows, escalation rules)
- Region-specific carrier info (UK=DPD, EU=UPS, AU=AuPost/StarTrack)
- The order value escalation thresholds ($200/$500)
- Cut-off times by country
- Return locations (AU→Villawood, UK→Coalville, FR/ES/IE→Born)

### 4. Structured ticket parsing
The #eu-uk-fulfillment channel uses a Request Manager bot that posts structured tickets like:

```
@username
What team do you belong to?
Sales
Have you checked the pinned FAQ's doc?
YES
Merchant Token
MLF9QBNZAW7XA
Order Number
ES-028968397
Country
ES
Order Date
4/10/26
Issue with the order (order MUST be over 200 GBP/EUR)
Order Not Delivered
Please provide more details of your query
UPS says delivered but seller claims seller has not received it.
```

Add a parser function `parse_eu_ticket(text: str) -> Dict` that extracts:
- `order_number` — the order number (GB-XXX, ES-XXX, etc.)
- `country` — country code
- `issue_type` — the issue category
- `details` — the free-text description
- `merchant_token` — if present
- `team` — which team submitted

Use this parsed data to enrich the triage response.

### 5. Region-aware order lookup
The existing `lookup_order()` function queries `DELIVERY_ORDERS` and `SHIPMENTS`. These tables already contain EU/UK/AU orders (they have GB-, FR-, ES-, IE-, AU- prefixes). No schema changes needed — just make sure the order number regex captures them.

### 6. Triage response format for EU/UK/AU
The bot's triage response should include:
- Order data (status, dates, tracking) — same as US
- **Region-specific SLA check** — compare actual transit days against the FAQ SLA table
- **Carrier-specific guidance** — DPD delivery attempts (UK), UPS access point (EU), AuPost depot hold (AU)
- **Recommended action** based on the FAQ decision tree:
  - Non-receipt + outside ship quote → "Contact carrier"
  - Non-receipt + no movement after carrier contact + 48h → "Place new order"
  - Partial receipt + 48h → "Place new order"
  - No tracking after 48h in "sent to warehouse" → "Escalate to LGX"
  - Address change for "Out for Delivery" → "Customer should contact carrier directly"
  - RTS → "Place new order if still wanted"
- **Order value escalation** — if order value > $200, flag for SAS escalation

## EU/UK/AU FAQ Content
Save this as `shared/eu_uk_au_faq.md`:

```markdown
# EU/UK/AU Fulfillment FAQ

## Customer Facing Ship Quotes (business days, M-F)

| Country | Standard | Expedited |
|---------|----------|-----------|
| UK | 1-2 days | 1 day |
| NI (Northern Ireland) | 3 days | 2 days |
| FR (France) | 4 days | 2 days |
| IE (Ireland) | 3-5 days | 1-2 days |
| ES (Spain) | 4-6 days | 2-3 days |
| AU (Australia) | 3-5 days | 1-3 days |
| AU Remote | 2+ weeks | 1-4 days |

AU Remote postcodes: Lord Howe (2898), Norfolk (2899), Christmas (6798), Cocos Keeling (6799)

WARRANTY orders for 1P payment devices ship expedited. Regulator will show "standard" — click tracking for details.
Warranty for Square accessories ships standard. We do not warranty 3P products (printers, paper, cash drawers).
Logistics will upgrade shipping only where it is the fault of the warehouse or carrier.

## Cut-Off Times
Orders in "sent to warehouse" before cutoff ship that day. After cutoff = next day.

| UK | FR | IE | ES | AU | SG |
|----|----|----|----|----|-----|
| 13:00 GMT | 15:30 CET | 15:30 CET | 15:30 CET | 14:00 AUST | 16:00 SST |

## Carrier Delivery Attempts

### UK - DPD
- B2C: 1 delivery attempt. If unavailable, card left + sent to parcel shop for 5 days.
- B2B: 2 delivery attempts, then returned to sender (RTS).
- DPD will contact recipient via email/phone to arrange delivery options.
- If no contact within that week, order is RTS.

### EU - UPS
- B2C: 1 delivery attempt + 5 days at Access Point (residential only).
- B2B: 3 attempts, then RTS.
- UPS determines B2B vs B2C based on customer input, internal data, and driver observations.

### AU - Australia Post
- 1 delivery attempt. If unsuccessful, card left + sent to depot for 10 days. If not retrieved, RTS.

### AU - StarTrack
- 2 delivery attempts. If unavailable, sent to local post office. Customer can manage delivery via AU Post website.

## Order Value Escalation (ALL markets, USD equivalent)

| Order Value | Action |
|-------------|--------|
| Under $200 | Help seller place new order |
| $200-$500 | Escalate to SAS |
| Over $500 | SAS to notify LGX (carrier credit only — lost order retrieval takes 2+ weeks) |

## Order Updates
- Tracking details: Check Regulator (https://regulator.sqprod.co/o/advanced-search?searchTarget=sqShopOrder) in Shipping section
- Once "sent to warehouse" in Regulator: NO changes possible (no adding/removing items, no address changes, no cancellations, no speed changes)
- If customer doesn't need it: Refuse delivery → RTS
- Backorders: If any item is backordered, the ENTIRE order is held. No partial shipments. Check go/backordered.

## Delivery Issues Decision Tree

1. **Non-Receipt (check tracking first!)**
   - Outside ship quote → Contact carrier
   - AU: Check if remote island (extended delivery times)
   - No movement after carrier contact + 48 hours → Place new order
   - Partial receipt (missing items) + 48 hours → Place new order
   - No tracking after 48 hours in "sent to warehouse" → Escalate to LGX

2. **Address Changes**
   - "Out for Delivery" → Customer contacts carrier directly
   - UK self-service doc: https://docs.google.com/document/d/1XZ9dwJ_bjpwkeBdrOySMkqr-_LxpY3ARYU21Cr-ZHME/edit
   - If carrier can't help → Refuse original order + place new order

## Returns Guidelines

### RTS (Returned to Sender)
- Place new order if still wanted. We CANNOT reship.
- Reasons: Customer didn't pick up at depot, incorrect address, stuck in network
- AU RTS: Processed using order number → triggers refund. If not, raise with lead.
- EU/UK RTS: Refunded based on returned_to_sender carrier message.

### Multiple Items / Single Return Label
- SHOP logic: 1 label per item
- If multiple items sent back under 1 label: items 2 & 3 processed as blind
- CS may non-urgently ping LGX to confirm items 2 & 3 returned
- CS still needs to force refund (we can't trigger without correct label)

### Northern Ireland Returns
- Contact LGX for return label

### Alternative Carrier Returns (not using Shop return label)
- Manual tracking and manual refund required
- Refunds not triggered when not following Shop return flow

### Waiting on Refund
- If tracking confirms delivered to return location, CS may trigger refund without alerting LGX
- Return locations: AU → Villawood | UK → Coalville | FR/ES/IE → Born

### Post-Receipt Issues
- Damaged items → CS FAQ return/warranty flow
- 3P products: UK/EU — not warrantied by Square. AU — follow Squarewise process.
- Wrong items → CS FAQ return flow
- Missing components → Verify inclusion, then return flow
- Item returned but lost in transit → Escalate to lead
- Item returned + processed but no refund → Refer to SHOP Simple Return Policy, escalate to lead
- New return label past return window → Contact #shop-xfn-requests
```

## Files to create/modify
- `shared/eu_uk_au_faq.md` — NEW (content above)
- `scripts/slack_listener.py` — modify:
  - `find_order_number()` — broaden regex to `[A-Z]{2}-\d{6,9}`
  - Add `_load_eu_uk_au_faq()` and `EU_UK_AU_FAQ` global
  - Add `parse_eu_ticket()` function
  - Add `_get_region_from_order()` helper (returns 'US', 'UK', 'EU', 'AU' based on prefix)
  - Update `_generate_playbook_response()` to inject EU FAQ when order is non-US
  - Update `format_order_response()` to include region-specific SLA comparison

## Testing
```bash
python3 -c "import ast; ast.parse(open('scripts/slack_listener.py').read()); print('OK')"
```

Test order number detection:
```python
assert find_order_number("GB-283041028") == "GB-283041028"
assert find_order_number("ES-028968397") == "ES-028968397"
assert find_order_number("AU-123456789") == "AU-123456789"
assert find_order_number("US-373216476") == "US-373216476"
assert find_order_number("FR-813579161") == "FR-813579161"
```

## Don't change
- The Snowflake connection logic
- The Databricks LLM endpoint
- The DM listener or learning commands
- The existing US triage logic (only extend, don't break)
