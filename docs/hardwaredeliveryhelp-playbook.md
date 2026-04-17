# #hardwaredeliveryhelp — Resolution Playbook

> **Purpose:** Operational reference for LGX-OPS-BOT to triage and respond to tickets in #hardwaredeliveryhelp.
> Based on 700+ tickets resolved by Oscar Saravia (BPO) from October 2025 – April 2026.

---

## 1. Ticket Types & Frequency

| Type | % of Tickets | Oscar Resolves? | Bot Can Handle? |
|---|---|---|---|
| **Order Status** | ~35% | ✅ Yes | ✅ Yes — query DELIVERY_ORDERS + SHIPMENTS |
| **Return** | ~28% | ⚠️ Partially — many reassigned | ⚠️ Triage only — returns need manual action |
| **Replacement** | ~22% | ✅ Yes | ⚠️ Triage only — needs Solid Shop access |
| **Change Address** | ~8% | ✅ Yes | ❌ No — requires CEVA/warehouse update |
| **BOPIS Order** | ~3% | ❌ Always reassigned | ❌ Always reassign |
| **Discount/Refund** | ~2% | ⚠️ Mixed | ❌ Reassign |
| **Fraud** | ~1% | ✅ Yes | ❌ Reassign |

---

## 2. Resolution Outcomes (from 700+ tickets)

| Outcome | % | Meaning |
|---|---|---|
| **Resolved** | ~84% | Oscar answered and closed |
| **Reassigned** | ~11% | Sent to another team (returns, BOPIS, GB orders) |
| **Duplicated** | ~3% | Same order re-submitted — mark as dupe |
| **No Response from Submitter** | ~2% | Oscar replied, submitter never followed up |

---

## 3. Resolution Playbooks by Ticket Type

### 3.1 Order Status (~35% of tickets)

**What the submitter asks:** "Where is order US-XXXXXXXXX?"

**Bot resolution steps:**
1. Query `LGX_OPS_BOT.WIGEON.DELIVERY_ORDERS` by ORDER_NUMBER
2. Query `LGX_OPS_BOT.WIGEON.SHIPMENTS` by ORDER_TOKEN (if needed for line-level detail)
3. Check `APP_HARDWARE.MART_LOGISTICS.RPT_SQ_DELIVERY_PERFORMANCE` for granular tracking

**Response template based on status:**

#### Status: DELIVERED
```
📦 Order {order_number} — Delivered ✅
• Ordered: {ordered_date}
• Shipped: {first_ship_date} from {facilities} via {carriers}
• Delivered: {first_delivery_date}
• Tracking: {tracking_numbers}
• Items: {total_items} item(s), {shipment_count} shipment(s)

The order shows as delivered. If the seller reports they didn't receive it,
this may be a porch piracy / misdelivery case — recommend filing a carrier claim.
```

#### Status: SHIPPED (Pending Delivery)
```
📦 Order {order_number} — In Transit 🚚
• Ordered: {ordered_date}
• Shipped: {first_ship_date} from {facilities} via {carriers}
• Estimated delivery: {estimated_delivery_date}
• Tracking: {tracking_numbers}
• Transit days so far: {current_date - first_ship_date}

{IF transit_days > 5 for ground OR transit_days > 3 for expedited:}
⚠️ This shipment appears delayed. Recommend contacting {carrier} with tracking
{tracking_number} to request a trace/investigation.

{IF transit_days > 10:}
🔴 This shipment is significantly overdue. Recommend filing a lost package claim
with {carrier} and issuing a replacement or refund.
```

#### Status: NOT SHIPPED (Processing)
```
📦 Order {order_number} — Processing ⏳
• Ordered: {ordered_date}
• Sent to warehouse: {sent_to_wh_date}
• Facility: {facilities}
• Processing days: {processing_days}

{IF processing_days > 2:}
⚠️ This order has been processing for {processing_days} business days.
Normal processing is 1-2 business days. Escalating to warehouse team.

{IF processing_days > 5:}
🔴 This order is significantly delayed in processing. May be a warehouse hold,
inventory issue, or address validation problem.
```

#### Status: NOT FOUND
```
⚠️ Order {order_number} — Not found in delivery system.

Possible reasons:
• Order was placed very recently and hasn't been sent to warehouse yet
• Order number may be incorrect — please verify
• This may be a return order (not an outbound shipment)
• For BOPIS orders, this channel cannot assist — please contact the retail team

cc @osaravia-bpo for manual investigation.
```

**When Oscar contacts carriers (External Emails column > 0):**
- ~10% of Order Status tickets require carrier email follow-up
- Typically for shipments stuck in transit 5+ days
- Oscar emails the carrier (FedEx, UPS, USPS, Purolator, DHL) requesting a trace
- Bot should flag these and cc Oscar for carrier outreach

---

### 3.2 Returns (~28% of tickets)

**What the submitter asks:** "Seller needs to return hardware" or "Return label needed"

**Key patterns from Oscar's data:**
- ~30% of return tickets get **reassigned** (highest reassignment rate of any type)
- Orders ending in `-WR` are warranty returns (e.g., `US-279660031-WR`)
- CA returns often reassigned (different process than US)
- GB returns **always** reassigned (different team handles UK)

**Bot triage steps:**
1. Query DELIVERY_ORDERS to confirm original order exists and was delivered
2. Check if order number has `-WR` suffix (warranty return)
3. Determine country (US, CA, GB)

**Response template:**
```
📦 Order {order_number} — Return Request

Original order details:
• Ordered: {ordered_date}
• Delivered: {delivery_date} to {city}, {state}
• Items: {total_items} ({unique_skus} SKU(s))
• Facility: {facilities}

{IF country == 'GB':}
🇬🇧 UK returns are handled by a separate team. Reassigning.

{IF order has -WR suffix:}
🔧 This is a warranty return. Return authorization needed.

{IF country == 'US':}
Return labels for US orders are generated through Solid Shop or CEVA Mobility.
cc @osaravia-bpo to generate the return label.

{IF country == 'CA':}
Canadian returns go through IMC (Purolator). cc @osaravia-bpo to coordinate.
```

**Tools Oscar uses for returns:**
- **Looker** — Check if hardware has been returned to warehouse
- **Regulator** — Verify return receipt
- **Solid Shop** — Approve refunds after return confirmed
- **CEVA Mobility** — Generate return labels (login: d8HuF@ze5cmTv3n / JuanMGTBPO)

**Return label carrier rules:**
- US orders from CVU → FedEx or USPS (check seller's location — islands/remote areas may need USPS)
- CA orders from IMC → Purolator
- If seller says FedEx unavailable → switch to USPS or UPS

---

### 3.3 Replacements (~22% of tickets)

**What the submitter asks:** "Order arrived damaged" or "Missing items" or "Wrong item received"

**Bot triage steps:**
1. Query DELIVERY_ORDERS to confirm delivery
2. Note delivery date and transit time (damage claims need to be filed within carrier's window)
3. Check if this order already had a replacement (duplicate detection)

**Response template:**
```
📦 Order {order_number} — Replacement Request

Original order:
• Delivered: {delivery_date}
• Carrier: {carriers}
• Tracking: {tracking_numbers}
• Items: {total_items}

{IF days_since_delivery > 30:}
⚠️ This order was delivered {days_since_delivery} days ago. Replacement eligibility
may be limited — cc @osaravia-bpo for review.

{IF carrier == 'CEVA' or facility == 'CVU':}
If this is a fulfillment error (wrong item, missing item), this will be logged
in the Warehouse Fulfillment & Return Accuracy Tracker.

cc @osaravia-bpo to process replacement through Solid Shop.
```

**Oscar's replacement process:**
1. Verify delivery in Looker/DELIVERY_ORDERS
2. If damaged in transit → log in CEVA Delivery Claims tracker
3. If warehouse error → log in Warehouse Fulfillment & Return Accuracy Tracker
4. Process replacement through Solid Shop
5. If carrier claim needed → email carrier (shows as External Emails > 0)

---

### 3.4 Change Address Requests (~8% of tickets)

**What the submitter asks:** "Need to update shipping address for order"

**Bot response:**
```
📦 Order {order_number} — Address Change Request

{IF order_status == 'SHIPPED' or order_status == 'DELIVERED':}
⚠️ This order has already shipped/delivered. Address cannot be changed.
Options: return and reorder, or file a redirect request with the carrier.

{IF order_status == 'PROCESSING':}
Address changes for orders in processing are handled through the warehouse.
cc @osaravia-bpo to submit the address update to CEVA.
```

**Oscar's process:**
- Address changes logged in [Square Seller Address Update Requests (CVU - CVC)](https://docs.google.com/spreadsheets/d/1Ny-8nV3udKI46CRfUcI15Ow49PeARHQkOYU6ps12nK4/edit)
- Must be submitted before order ships
- CVU (US) and CVC (CA) have separate processes

---

### 3.5 BOPIS Orders (~3% of tickets)

**Always reassign.** Oscar reassigns 100% of BOPIS tickets.

```
📦 Order {order_number} — BOPIS (Buy Online, Pick Up In Store)

BOPIS orders are handled by the retail operations team, not the fulfillment team.
Reassigning to the appropriate team.
```

---

## 4. Escalation & Reassignment Rules

### Always Reassign:
- **BOPIS orders** → Retail team
- **GB/UK orders** → EU/APAC team (Jennifer Opland, jopland@squareup.com)
- **Discount requests** → Usually reassigned
- **Fraud cases** → Fraud team (rare, ~1%)

### Reassign After Triage:
- **Returns with -WR suffix** → May need warranty team
- **CA returns** → Sometimes different process
- **Orders not in system** → May be retail/enterprise orders

### Oscar Handles Directly:
- US/CA order status lookups
- US/CA replacement processing
- Address change requests (pre-shipment)
- Carrier follow-ups via email
- CEVA delivery claims
- Warehouse accuracy tracking

---

## 5. Key Systems & Tools

| Tool | Purpose | Used For |
|---|---|---|
| **Looker** | Order tracking, delivery status, return receipt | Order Status, Returns |
| **Solid Shop** | Process refunds, replacements | Replacements, Refunds |
| **CEVA Mobility** | Warehouse management, return labels | Returns, Address Changes |
| **Amazon Tool (US/CA)** | Invoice disputes, shortage claims | Weekly disputes |
| **Regulator** | Return verification | Returns |
| **Mainchain** | Tracking tool | Order Status |

### Key Looker Report:
- [INBOUND GR DAILY (NA / EU / APAC)](https://square.cloud.looker.com/looks/96034?toggle=fil)

---

## 6. Key Trackers & Documents

| Tracker | Purpose | Link |
|---|---|---|
| Warehouse Fulfillment & Return Accuracy | Log fulfillment errors, track returns | [Link](https://docs.google.com/spreadsheets/d/1ajl80UK5hhkK0K05sqglpztflmwYG2qDRamau1YHsng/edit) |
| Address Update Requests (CVU/CVC) | Address changes for US/CA | [Link](https://docs.google.com/spreadsheets/d/1Ny-8nV3udKI46CRfUcI15Ow49PeARHQkOYU6ps12nK4/edit) |
| CEVA Delivery Claims | Lost/damaged in transit claims | [Link](https://docs.google.com/spreadsheets/d/1h6DZwqmBXYVkneJz53K9n3U8sEEwKCWsjaG-B0cP0Og/edit) |
| Amazon US/CA Dispute Tracker | Amazon shortage/dispute/BOL | [Link](https://docs.google.com/spreadsheets/d/1dqHN2px2viB_afDJ9giNll0cCAnEGcEv3Tl87pqN1Ho/edit) |
| Returns Tracker (BPO) | RMA tracking | [Link](https://docs.google.com/spreadsheets/d/1rXePiVmxCVEXjd-2z2-AM4FkBS8GIcC5ygMMXMce6cA/edit) |
| Outbound Invoice Reconciliation | Invoice matching | [Link](https://docs.google.com/spreadsheets/d/1e-R6oRbk5_IwPl-s_WVtwMSPFt-p2_ix_Cm2n8B1Uiw/edit) |
| UPS-MI / USPS Invoice Consolidation | Carrier invoice summary | [Link](https://docs.google.com/spreadsheets/d/1aCFFiUGCFjzbWxHa5Idn7aZxOomXEPOaa9g1aSHPapE/edit) |
| Daily GR Template (US/CA) | Inventory receipt processing | [Link](https://docs.google.com/spreadsheets/d/1KOu76fWNpTEjTsaD-qUKRE6v__c4JEB_Go7T0ZoI0g4/edit) |
| Daily GR Template (EU/APAC) | EU inventory receipt | [Link](https://docs.google.com/spreadsheets/d/1hIxRsq9YqxGPkrORHFIngyQLsOmNXAxRjWrxyDsEoz4/edit) |
| Daily GR Template (Japan) | JP inventory receipt | [Link](https://docs.google.com/spreadsheets/d/1m6otteqi1O8HnIGfIpuT0Y_n9Y6uipkXYcVgJYvYrLs/edit) |

### SOPs:
- [Block Return Authorization (SOP)](https://docs.google.com/document/d/1pcWLPEeB7Dg9E1c3AUaonzSoTeYmss1lmVqq56Fk4v0/edit)
- [BPO EU/APAC Delivery Help Process](https://docs.google.com/document/d/1w6ETJpigYUMVB_K1N0z1lEDTSOvEWZa2zCxQqll2vzE/edit)
- [Daily GR Process / NLD](https://docs.google.com/document/d/1VGwvzDKUTj7gK9CcES2pbNhvaYgMRr6KfAo2HandjJU/edit)
- [Warehouse Fulfillment Accuracy Photos](https://docs.google.com/document/d/1BK8HzsQxBtIb3tI46mt1xitdwGp0Mov5FkhJQ1fssHg/edit)

---

## 7. Carrier-Specific Knowledge

### US Carriers:
| Carrier | Code | Typical Use | Claim Process |
|---|---|---|---|
| **USPS** | usps | eCommerce ground, PO Box | File at usps.com, 15-day investigation |
| **FedEx** | fedex | Expedited, high-value | File at fedex.com or call 1-800-463-3339 |
| **UPS** | ups | Ground, some expedited | File at ups.com |
| **UPS-MI** | ups-mi | UPS Mail Innovations (lightweight) | File through UPS |

### CA Carriers:
| Carrier | Code | Typical Use |
|---|---|---|
| **Purolator** | purolator-v2 | All CA shipments from IMC |

### Shipping Methods:
| Code | Meaning |
|---|---|
| G3DAYP | 3-Day Priority |
| GGRNDP | Ground |
| G2DAYP | 2-Day Priority |
| GNXDYP | Next Day Priority |

### Facilities:
| Code | Location | Markets |
|---|---|---|
| **CVU** | CEVA US (California) | US orders |
| **CVC** | CEVA Canada | CA orders |
| **IMC** | Ingram Micro Canada | CA orders |
| **IMU** | Ingram Micro US | US orders (some) |
| **GBR** | UK facility | GB orders |
| **NLD** | Netherlands facility | EU orders |
| **SCH** | Schenker | EU/APAC |

---

## 8. Timing & SLA Thresholds

### Processing Time (Order → Ship):
- **Normal:** 1-2 business days
- **Warning:** 3-4 business days → flag for warehouse follow-up
- **Critical:** 5+ business days → escalate immediately

### Transit Time (Ship → Delivery):
- **Ground (US):** 3-7 business days typical
- **3-Day Priority:** 3 business days
- **2-Day Priority:** 2 business days
- **Next Day:** 1 business day
- **Ground (CA):** 3-5 business days
- **Warning:** 2x expected transit time
- **Lost package threshold:** 10+ business days past estimated delivery

### Carrier Claim Windows:
- **USPS:** File after 15 days, within 60 days of ship date
- **FedEx:** File within 60 days of ship date (21 days for freight)
- **UPS:** File within 60 days of delivery date
- **Purolator:** File within 30 days

---

## 9. Duplicate Detection

Oscar's data shows ~3% of tickets are duplicates. Detection rules:
- Same order number submitted within 7 days → likely duplicate
- Same order number with different ticket types → may be escalation (not dupe)
- Orders with `-WR` suffix are warranty returns of the same order (not dupes)

**Bot behavior on duplicates:**
```
ℹ️ Order {order_number} was already addressed in this channel on {previous_date}.
Previous status: {previous_resolution}. Let me check for any updates since then.
```

---

## 10. Escalation Contacts

| Role | Person | Contact | Handles |
|---|---|---|---|
| **BPO Lead** | Oscar Saravia | @osaravia-bpo (U02DXNZF8SF) | US/CA tickets, carrier claims, warehouse issues |
| **DRI — Channel** | Dane Steffy | @dsteffy | Channel oversight, replacements, RMAs |
| **DRI — Warehouse** | Alvin Leung | @aleung | CEVA claims, address updates, delivery claims |
| **DRI — Invoice** | Molly Kaess | @mkaess | Invoice consolidation, UPS billing |
| **DRI — EU/APAC** | Jennifer Opland | jopland@squareup.com | GBR/NLD/JP orders |
| **DRI — GR Reports** | Jeremy Wittmeier | @jwittmeier | Inventory receipt (US/CA) |
| **DRI — Invoice Recon** | Vanessa Young | @vyoung | Outbound invoice reconciliation |
| **EU/APAC Billing** | Julie / Alexander | — | EU/APAC invoice accounting |

---

## 11. Bot Response Guidelines

### Tone:
- Professional, concise, factual
- Lead with the data (order status, dates, tracking)
- Always provide tracking numbers when available
- Use emoji sparingly: ✅ delivered, 🚚 in transit, ⏳ processing, ⚠️ warning, 🔴 critical

### Always Include:
- Order number
- Current status
- Key dates (ordered, shipped, delivered or estimated)
- Tracking number(s)
- Carrier name
- Facility

### Always cc Oscar When:
- Returns need label generation
- Replacements need Solid Shop processing
- Address changes need warehouse coordination
- Carrier email follow-up needed
- Order not found in system
- Any GB/BOPIS/Fraud/Discount ticket

### Never Do:
- Process refunds (requires Solid Shop access)
- Generate return labels (requires CEVA Mobility)
- Contact carriers directly (Oscar handles via email)
- Handle BOPIS orders
- Handle GB/UK orders
- Make promises about delivery dates beyond what tracking shows
