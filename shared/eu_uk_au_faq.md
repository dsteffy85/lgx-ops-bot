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
