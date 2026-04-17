# Resource Links - Maintenance Reference

> This is NOT a user-facing article. This file is a centralized reference for all URLs and links used across the Inky knowledge base. When a link changes, update it here and in the articles listed in the "Referenced In" column.

Last reviewed: 2026-03-25

## Link Reference Table

| Link Name | URL | Referenced In |
|---|---|---|
| Commercial Invoice Template | https://docs.google.com/spreadsheets/d/1xGH1Qbui51el2OJyXCvYKpK_F56i73GIwhiypiFyNZ8/edit?gid=1786971535#gid=1786971535 | 01, 04, 09 |
| HS Code Database | go/hscodes | 00, 01, 03, 04, 05, 09 |
| Classification Request | go/classificationrequest | 00, 03, 08, 13 |
| Transit Time Standards | go/logisticscommit | 00, 05, 08 |
| Shipment Tracking Dashboard | https://square.cloud.looker.com/dashboards/31346 | 00, 05, 08 |
| Inventory Report | https://square.cloud.looker.com/looks/76969 | 00, 05, 08 |
| Holiday Calendar | https://docs.google.com/spreadsheets/d/19Q59q7Fr4Z37ENihaPEe1w-8e46_A0_guxk7C1tRF6E/edit#gid=2145583215 | 05 |
| Team Email | tradecompliance@squareup.com | All articles |
| Slack Channel | #ask-logistics | All articles |

| Snowflake | go/snowflake | 05 |
# How to Ship Internationally from Block

## Overview
All international shipments from Block require a commercial invoice and proper customs documentation. This article covers the basics of getting a shipment out the door.

## Steps to Ship Internationally

### 1. Prepare a Commercial Invoice
Every international shipment needs a commercial invoice. Use the [Block Commercial Invoice Template](https://docs.google.com/spreadsheets/d/1xGH1Qbui51el2OJyXCvYKpK_F56i73GIwhiypiFyNZ8/edit?gid=1786971535#gid=1786971535) - make a copy and fill out the "US Export" tab.

Include:
- Product description
- Quantity
- Unit value (fair market price)
- HS code (check go/hscodes for the US HTS code)
- Country of origin

If accessories like cables and power supplies are part of a single functional unit (e.g., a kiosk kit), they can be listed on the same line as the main product. The line value should reflect the fair market price of all items combined. If accessories are separate SKUs or different quantities, list them on separate lines.

### 2. Get a Shipping Label
Submit a ship request to the Block mailroom for a FedEx label. Include the commercial invoice with your request.

### 3. Determine the Right Shipping Terms
- If Block has an importing entity in the destination country, we can ship DDP (Block handles customs and pays duties).
- If Block does not have an importing entity, ship DAP (receiver handles customs clearance). See the "Where Block Can and Cannot Act as Importer" article for details.

### 4. Check HS Code
Look up the US HS code for your product at go/hscodes. The US HS code goes on the commercial invoice. The destination country determines their own import classification at time of entry.

If the product isn't listed in go/hscodes, please submit a classification request at go/classificationrequest with product details.

## Important: Do Not Hand Carry
Hand carrying products across borders is a commercial shipment subject to import and export regulations. Anyone hand carrying on behalf of Block is representing the company and is required to file a formal customs declaration, including paying any duties and taxes.

Ship via FedEx IP or IPF instead. Transit time is typically 1-3 business days for most international destinations.

## Need Help?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Where Block Can and Cannot Act as Importer

## Overview
Whether Block can act as the Importer of Record (IOR) depends on whether we have a legal entity in the destination country. This determines the shipping terms (DDP vs DAP) and who handles customs clearance.

## Countries Where Block Acts as IOR (DDP)
Block has importing entities in the following countries and can act as Importer of Record:
- **United States**
- **United Kingdom**
- **Netherlands**
- **Ireland**
- **Canada**
- **Australia**
- **Japan**

For shipments to these countries, Block handles customs clearance and pays duties and taxes. Ship DDP (Delivered Duty Paid).

## Countries Where Block Cannot Act as IOR (DAP)
For all other countries, Block does not have an importing entity. This includes (but is not limited to):
- France
- Italy
- Spain
- Germany
- Taiwan
- Korea
- India
- China

For these destinations, ship DAP (Delivered at Place). Block covers the transport cost door-to-door, but the receiver acts as the importer and handles customs clearance on their end.

**Before shipping DAP, always confirm with the receiver that they are willing and able to act as importer.** If the receiver can't import, the shipment will get stuck in customs.

## EU Shipments from Outside the EU
Block can only import into the EU through our entities in Ireland (IE) or the Netherlands (NL). For other EU countries:

**Option 1:** Ship to Block's NL or IE warehouse, then forward within the EU as an intra-EU transfer (no additional customs clearance needed within the EU).

**Option 2:** Ship DAP directly to the destination. The receiver handles customs clearance as importer.

## Specific Country Notes

### India
Ship DAP. Nomiso handles import clearance on our behalf in India.

### France
Block has no importing entity in France. The receiver (e.g., a lab or partner) needs to act as IOR. Block can pay duties and taxes via our FedEx account, but the receiver still needs to be on the customs declaration as importer.

### UK
Block has entity in the UK and can act as IOR. Shipments to the UK should be straightforward.

## What Are DDP and DAP?
- **DDP (Delivered Duty Paid):** Block pays for transport AND acts as importer. Block handles customs clearance and pays all duties and taxes.
- **DAP (Delivered at Place):** Block pays for transport door-to-door, but the receiver acts as importer and handles customs clearance. The receiver is responsible for duties and taxes unless other arrangements are made.

## Sanctioned and Embargoed Countries
Block cannot ship to countries subject to comprehensive U.S. sanctions. This includes North Korea, Iran, Cuba, Syria, and the Crimea/Donetsk/Luhansk regions of Ukraine. This is a legal prohibition, not a logistics limitation. If you're unsure whether we can ship to a destination, please check with Inky or the trade compliance DRI.

## Questions?
If you're not sure whether Block has an entity in a specific country, or need help figuring out the right shipping terms, check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# HS Codes and Product Classification

## Overview
Every product shipped internationally needs an HS (Harmonized System) code for customs classification. Block maintains a classification database with US HTS codes for our products.

## How to Find an HS Code

### Step 1: Check go/hscodes
The Block classification database at go/hscodes is the single source of truth for our product classifications. Look up your product there first.

### Step 2: If the Product Isn't Listed
If your product isn't in go/hscodes, please submit a classification request at go/classificationrequest. Include:
- Product name and description
- What it does (intended use)
- Part number or SKU if available
- Any relevant product documentation

The trade compliance team will classify the product and add it to the database.

## Which HS Code to Use

### Shipping from the US
Use the US HTS code from go/hscodes on your commercial invoice. The destination country determines their own import classification at time of entry - that's the responsibility of the importer in the destination country.

### Importing into a Country Where Block is IOR
When Block acts as importer (US, UK, NL, IE, CA, AU, JP), we need the destination country's HTS code. The trade compliance team manages these classifications.

### EU Shipments
NL HS codes can generally be used for IE imports (they're likely the same within the EU tariff schedule).

## Classification Should Happen Before Shipping
HS codes need to be confirmed before anything ships internationally. If a shipment is already stuck in customs because of a classification issue, focus on helping resolve it first. Then gently let them know about the process for next time. Don't be preachy or make them feel bad - this is a common situation and they're coming to you for help.

When someone has a shipment stuck in customs needing classification:
1. Acknowledge the situation and help them move forward
2. Direct them to submit a classification request at go/classificationrequest right away so the team can work on it
3. Point them to the trade compliance DRI (see routing table) to help resolve the current hold
4. Once the immediate issue is addressed, mention that getting the HS code confirmed before shipping helps avoid customs holds - and go/classificationrequest is the place to do that for future shipments

Keep it supportive. "For next time, if you submit a classification request before the shipment ships, we can usually avoid customs holds like this" - not "you should have done this before shipping."

## Important Notes
- Do not guess on HS codes. An incorrect classification can result in delays, penalties, or seizure of goods.
- If you're unsure, please submit a request at go/classificationrequest or check the DRI routing table for the trade compliance contact.
- HS codes may change over time due to regulatory updates. Always check go/hscodes for the current classification.

## Questions?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Commercial Invoice Guide

## Overview
A commercial invoice is required for every international shipment. It tells customs what's in the box, what it's worth, and where it came from.

## Template
Use the [Block Commercial Invoice Template](https://docs.google.com/spreadsheets/d/1xGH1Qbui51el2OJyXCvYKpK_F56i73GIwhiypiFyNZ8/edit?gid=1786971535#gid=1786971535) - make a copy and fill out the "US Export" tab.

## What to Include
- **Product description** - clear enough for customs to understand what it is
- **Quantity** - number of units
- **Unit value** - fair market price per unit (not cost, not internal transfer price)
- **Total value** - quantity x unit value
- **HS code** - US HTS code from go/hscodes
- **Country of origin** - where the product was manufactured
- **Shipper and consignee** - who's sending and who's receiving

## Accessories and Kits
If accessories (cables, power supplies, mounting hardware) are part of a single functional unit - like a kiosk kit - they can be listed on the same line as the main product. The line value should be the fair market price of all items combined.

If accessories are separate SKUs, separate orders, or different quantities than the main unit, list them on separate lines with their own HS codes and values.

## Common Mistakes
- **Missing HS code** - always include one. Check go/hscodes.
- **Undervaluing** - use fair market value, not $0 or $1. Even samples and prototypes need a realistic declared value.
- **Missing country of origin** - required for every line item.
- **Vague descriptions** - "electronic device" isn't enough. Be specific: "Point of sale terminal with touchscreen display."

## Questions?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Tracking Shipments and Inventory

## Overview
Block has several tools for tracking inbound shipments and inventory. Start with the dashboard for quick checks, and use Snowflake for more detailed analysis.

## Primary Tools

### Inbound Shipment Dashboard
Your main tracking tool for products in transit:
https://square.cloud.looker.com/dashboards/31346

Search by:
- **Product SKU** (most reliable)
- **Purchase order number**
- **Shipment ID**

### Current Inventory Report
See what's currently available:
https://square.cloud.looker.com/looks/76969

### Shipping Time Standards
Official transit time commitments by lane:
go/logisticscommit

Typical timeframes (add buffer for planning):
- **Air freight:** 1-3 weeks
- **Ocean freight:** 4-8 weeks
- **Ground:** 1-2 weeks

Check the holiday calendar for periods when shipping slows down:
https://docs.google.com/spreadsheets/d/19Q59q7Fr4Z37ENihaPEe1w-8e46_A0_guxk7C1tRF6E/edit#gid=2145583215

## Understanding Shipment Milestones
Each milestone tells you where your products are:

1. **Booking Confirmation** - Freight forwarder accepted the shipment request
2. **Actual Pickup** - Products physically collected from factory
3. **Departure** - Products left origin port/airport
4. **Arrival** - Products arrived at destination port/airport
5. **Delivery** - Products physically delivered to warehouse
6. **Received at 3PL** - Warehouse finished processing, inventory available for orders

## Important: Delivery Does Not Equal Availability
Products arriving at the warehouse still need to go through receiving before they're available for orders:
- **With ASN (Advanced Shipping Notice):** 2-3 business days
- **Without ASN:** 5-7 business days (manual serial number scanning required)

## Red Flags to Watch For
If you see any of these, reach out to the appropriate DRI (see routing table):
- **Estimated delivery date has passed but no actual delivery date** - shipment may be delayed or data not updated
- **Multiple milestones missing** - shipment may not be moving as planned
- **Large gap between estimated and actual dates** - significant delay that may need investigation

## Using Snowflake for Detailed Tracking
For more detailed analysis, you can query shipment data directly in Snowflake (go/snowflake). The main shipment tables are in ORACLE_ERP.SCM.

If you use Goose (Block's AI assistant), you can ask it to query Snowflake for you in plain English - no SQL knowledge needed. Try something like "show me all open shipments for SKU X" or "what's the status of PO 12345?" Goose can pull the data, filter it, and summarize what you need.

## Questions?
If you can't find your shipment, data looks wrong, or you're seeing red flags, check the DRI routing table for the right person to tag. Include the SKU, shipment ID, and what you've already checked - that helps us help you faster.
# Export Controls and Restricted Items

## Overview
Some Block products and components are subject to export controls. These regulations restrict where certain items can be shipped and require advance review before export.

## Key Points
- Export compliance review is required BEFORE shipping controlled items. Do not wait until shipment day.
- Some items are export controlled and are NOT eligible for hand carry under any circumstances.
- Controlled items require specific documentation and may need an export license depending on the destination.

## What to Provide for Export Review
If you're shipping something that may be controlled, please provide:
- Item description and detail
- Intended use
- Quantity
- Destination country
- End user (who will receive and use the item)

## How to Get Help
Export compliance questions should go to the trade compliance DRI (see routing table), or email tradecompliance@squareup.com, with the details above.

Do not attempt to self-classify items for export control purposes. The trade compliance team will determine the ECCN (Export Control Classification Number) and advise on any licensing requirements.

## Common Scenarios
- **Shipping prototypes or engineering samples internationally** - these still require export review, even if they're not finished products
- **Shipping to labs for certification testing** - same rules apply. Provide item details and destination.
- **Shipping to countries with sanctions or restrictions** - always check with the trade compliance team first

## Questions?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com. The team would rather review something that turns out to be fine than have something ship without proper clearance.
# Warehouse Receiving and Processing

## Overview
When products arrive at a Block warehouse (3PL), they go through a receiving process before they're available for orders. Physical delivery does not equal inventory availability.

## Receiving Timeline
- **With complete ASN (Advanced Shipping Notice):** 2-3 business days
- **Without ASN:** 5-7 business days

The difference is significant. Without an ASN, the warehouse has to manually scan every individual serial number, which takes much longer.

## What Happens After Delivery
1. **Physical delivery** - boxes arrive at the warehouse dock
2. **Documentation check** - warehouse verifies the ASN (packing slip with serial numbers)
3. **Processing** - if ASN is complete, serial numbers are captured automatically. If not, manual scanning is required.
4. **Physical count** - warehouse counts and verifies everything
5. **Quality check** - some products require inspection
6. **System update** - products added to available inventory

## What Different Statuses Mean
- **"Bad Pallets"** - physical damage during shipping, needs repair or rework
- **"ASN Missing"** - no packing slip, warehouse doesn't know what's inside. This causes significant delays.
- **"SSR" (Special Stock Requirement)** - quality inspection needed before inventory release
- **"Partially Received"** - large shipment being processed in batches

## What is an ASN?
An ASN (Advanced Shipping Notice) is generated from the factory packout report and includes:
- SKU number
- Serial number for each unit
- Carton ID
- Pallet ID
- Shipment ID

Block maintains end-to-end serial number visibility for all products. The ASN is what makes automated receiving possible. Without it, the process slows down significantly.

## Questions?
If products were delivered but aren't showing as available and it's been longer than expected, check the DRI routing table for the right warehouse receiving contact for your region. Include the shipment ID and delivery date so they can check on the receiving status.
# How to Engage the Logistics Team

## Overview
The logistics team supports all of Block's hardware shipping, customs, trade compliance, and fulfillment operations. Here's how to get help.

## Where to Go

### Ask Inky First
Inky (Block's logistics AI assistant) can answer many common questions instantly — HS codes, shipping terms, country requirements, tracking help, and more. Try Inky as a first stop before reaching out to the team directly.

### #ask-logistics (Slack)
For questions Inky can't answer, reach out to the logistics team in #ask-logistics. The team monitors this channel and targets a 24-hour response SLA.

### tradecompliance@squareup.com
For customs, trade compliance, and classification questions that need email follow-up or involve external partners (brokers, freight forwarders, labs).

## Before You Post: Try Self-Service First
You may be able to find the answer faster on your own:
- **HS code lookup:** go/hscodes
- **Submit a classification request:** go/classificationrequest
- **Shipment tracking:** https://square.cloud.looker.com/dashboards/31346
- **Transit time standards:** go/logisticscommit
- **Current inventory:** https://square.cloud.looker.com/looks/76969

## When You Do Post, Please Include
The more context you provide upfront, the faster we can help:
- **What you're trying to do** - ship something, track something, classify something, etc.
- **What you've already checked** - "I looked at the dashboard and the shipment isn't showing up"
- **Specific details** - SKU numbers, shipment IDs, tracking numbers, dates, destinations
- **Business impact** - is this urgent? Is there a customer or program deadline?
- **Screenshots** if they help explain the issue

## What Not to Do
- Please don't send "Hi" and wait for a response. Just include your question in the first message.
- Please don't ask the same question in multiple channels. Pick #ask-logistics or email, and we'll route it from there.

## Urgency
If something is truly urgent (shipment stuck in customs, critical delivery at risk), please say so explicitly. We prioritize based on business impact.

## Questions?
If you're not sure where to start, try Inky or reach out to the logistics team in #ask-logistics. They'll point you in the right direction.
# Hand Carries: Why We Don't Do Them

## Overview
Hand carrying Block products across international borders is not allowed. This comes up frequently with engineering samples, prototypes, and lab shipments, so it's worth understanding why.

## Why Not?
Anyone hand carrying products on behalf of Block is representing the company and is required to file a formal customs declaration, including paying any duties and taxes. This applies even for small items, prototypes, and samples.

Hand carries create compliance risk because:
- The person carrying may not know the correct HS code, value, or export classification
- Some items are export controlled and require advance review
- Customs declarations are legally binding - errors can result in penalties for Block
- There's no documentation trail for the company's records

## What to Do Instead
Ship via FedEx IP (International Priority) or IPF (International Priority Freight). Transit time is typically 1-3 business days for most international destinations. It's fast, documented, and compliant.

For shipments that need to arrive quickly:
1. Prepare a commercial invoice using the [Block Commercial Invoice Template](https://docs.google.com/spreadsheets/d/1xGH1Qbui51el2OJyXCvYKpK_F56i73GIwhiypiFyNZ8/edit?gid=1786971535#gid=1786971535)
2. Submit a ship request to the mailroom for a FedEx label
3. Include the HS code from go/hscodes on the commercial invoice

## But It's Just a Small Sample...
The size or value of the item doesn't change the requirement. A single prototype board and a full pallet of finished goods are both commercial shipments under customs law.

## Questions?
If you're in a time crunch and need to get something somewhere fast, check the DRI routing table for the freight forwarder contact. For compliance questions about what can and can't be shipped, check the routing table for the trade compliance contact, or email tradecompliance@squareup.com.
# Temporary Imports and Special Customs Programs

## Overview
Some countries offer customs relief programs for goods imported temporarily for testing, development, or exhibition purposes. These include temporary admission, testing relief, ATA Carnets, and similar mechanisms.

## Block's Position
Block does not currently manage temporary import programs. These programs come with tracking, audit, documentation, and re-export obligations that add a large amount of complexity and cost to manage. We have limited resources for our import programs and don't prioritize these today because they cost more than we gain from them.

## What This Means in Practice
If you're shipping products to a lab, partner, or event and thinking about temporary import relief:

- **The receiving party (lab, partner, etc.) is better positioned to manage this.** They handle these types of imports regularly and should be more familiar with the available options than we are. They likely already manage temporary import programs for other clients.
- **The receiving party should know what options are available** for their country and should be able to import quicker and cheaper than if Block tried to set something up.
- **Block can still pay duties and taxes** via our FedEx account even when the receiver acts as importer. The financial burden doesn't have to fall on them - but the import management does.

## Recommended Approach
1. Ask the receiving party what import options they can support
2. Once they come back with what they're able to do, the logistics team can help figure out the best path
3. Where Block has importing entities (US, UK, NL, IE, CA, AU, JP), we have options to route through those countries if needed

## Why Not Just Do It Ourselves?
Temporary import programs require:
- Individual tracking of every unit
- Re-export within a specific timeframe
- Audit-ready documentation proving compliance with program requirements
- Penalties (full duties plus fines) if anything falls through the cracks - a unit doesn't get returned on time, documentation is incomplete, etc.

For a lean team shipping relatively small quantities of samples across multiple countries, the administrative overhead and risk outweigh the duty savings.

## Questions?
If you're working through a shipping scenario and need help evaluating options, check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com. The team is happy to help figure out the best approach once we know what the receiving party can support.
# Tariffs and Duties: The Basics

## What Are Duties and Tariffs?

Duties and tariffs are taxes imposed on goods when they cross an international border. They're collected by the destination country's customs authority at the time of import. If Block ships hardware from a factory in China to a warehouse in the United States, U.S. Customs and Border Protection (CBP) assesses and collects duties on that shipment before it's released.

## Who Pays?

Who pays duties depends on the shipping terms (Incoterms) agreed upon for the shipment:

- **DDP (Delivered Duty Paid):** Block pays all duties and import taxes. The receiver doesn't deal with customs costs.
- **DAP (Delivered at Place):** The receiver is responsible for paying duties and import taxes upon arrival.

Shipping terms are governed by the sales agreement between Block and the buyer or seller. In the absence of a sale (engineering samples, prototypes, lab shipments, etc.), incoterms should be mutually agreed upon between the shipper and receiver before anything ships. For guidance on which terms to use, check the DRI routing table for the trade compliance contact.

## Why We Can't Quote Specific Rates

Duty rates are not a simple lookup. The rate that applies to a given shipment depends on a combination of factors:

- **Product classification (HS code)** - what the product is, at a granular technical level
- **Country of origin** - where the product was manufactured or substantially transformed
- **Destination country** - each country maintains its own tariff schedule
- **Trade agreements** - preferential rates may apply under certain free trade agreements
- **Trade policy actions** - additional duties may be layered on top of base rates

The current U.S. tariff environment is particularly complex. Multiple overlapping trade policy actions are in effect - including IEEPA tariffs, Section 301 tariffs (China), Section 232 tariffs (steel/aluminum), and antidumping/countervailing duties (ADD/CVD) - each with different scopes, exclusions, and rates. These change frequently and require expert judgment to apply correctly.

Because of this complexity, Inky will not provide specific duty rates or estimates. For rate questions, contact the trade compliance team directly.

## Additional Taxes: VAT, GST, and Other Import Taxes

Many countries charge additional taxes on imports beyond duties - most commonly:

- **VAT (Value Added Tax)**
- **GST (Goods and Services Tax)**
- **Consumption taxes**

These taxes are assessed at import and can be significant. However, VAT/GST registration, recovery, and compliance are not managed by the logistics or trade compliance team. If you have questions about VAT, GST, or other tax obligations, please reach out to the **Tax team**.

## Questions?

Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Marking and Country of Origin Requirements

## What Is Country of Origin Marking?

Country of origin (COO) marking is a legal requirement to label imported goods with the country where they were manufactured or substantially transformed. This tells customs authorities and end users where a product comes from.

## U.S. Customs Marking Requirements

Under 19 U.S.C. Section 1304, every article of foreign origin imported into the United States must be marked with its country of origin. The marking must be:

- **Conspicuous** - easily found by a casual observer
- **Legible** - readable without effort
- **Permanent** - able to survive normal handling and use
- **In English** - for goods entering the U.S.

Common acceptable formats include:

- "Made in [Country]"
- "Assembled in [Country]"
- "Product of [Country]"

Failure to properly mark goods can result in additional duties, penalties, or shipment holds at the border.

## CBP Marking vs. FTC Origin Claims - Two Separate Frameworks

This is an important distinction that often causes confusion:

**CBP marking requirements** (19 U.S.C. Section 1304) are a customs and regulatory obligation. They govern what must be physically marked on imported goods to clear customs. These are enforced by U.S. Customs and Border Protection.

**FTC origin claims** ("Made in USA," "Assembled in United States," etc.) are a consumer-facing marketing standard. They govern what origin claims a company can make to consumers on packaging, marketing materials, and product labeling. These are enforced by the Federal Trade Commission and have different legal standards than CBP marking.

A product can comply with CBP marking requirements while still needing careful analysis before any FTC origin claim is made - and vice versa. The two frameworks operate independently.

## Don't Self-Serve on Marking or Origin Decisions

Country of origin determination and marking requirements are product-specific and legally consequential. Do not make marking decisions without consulting the trade compliance team. This includes:

- Determining the correct country of origin for a product
- Choosing marking language or placement
- Making any "Made in" or "Assembled in" claims on packaging or marketing materials

## Questions?

Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Setting Up a New Inbound Shipping Lane

## What Is a "Lane"?

A lane is an origin-destination pair for shipping - for example, Shenzhen to Indianapolis, or Ho Chi Minh City to Rotterdam. A "new lane" means Block is shipping from a new origin country, working with a new supplier, or routing to a new destination for the first time.

## Engage the Logistics Team Early

Before the first shipment ships - not after it's stuck in customs.

New lanes involve regulatory, operational, and financial considerations that need to be evaluated before goods move. Engaging the logistics team early prevents delays, unexpected costs, and compliance issues.

## What the Logistics Team Will Evaluate

When you bring a new lane to the team, here's what gets assessed:

- **Import entity** - Does Block have an Importer of Record (IOR) in the destination country?
- **Export controls** - Are there restrictions on shipping from or to these countries?
- **HS classification** - Are the products classified? If not, submit a request at go/classificationrequest.
- **Customs broker** - Do we have a broker set up in the destination country?
- **Freight forwarder** - Do we have a forwarder covering this lane?
- **Shipping terms** - DDP vs. DAP, based on entity availability and lane specifics.
- **Transit time** - What's realistic? Air vs. ocean vs. ground options and tradeoffs.
- **Documentation** - What's required? Commercial invoice, packing list, certificates of origin, etc.
- **Regulatory requirements** - Country-specific import rules like licenses, permits, certifications, or product registrations.
- **Duties and taxes** - Estimated landed cost impact for budgeting and planning.
- **Sanctions screening** - Are there any trade restrictions involving these countries or parties?

## How to Engage

Reach out to the freight forwarder and trade compliance DRIs (see routing table) with the following details:

1. **Origin** - country and city/region if known
2. **Destination** - country and specific site/warehouse
3. **Product** - what's being shipped (hardware, components, materials, etc.)
4. **Estimated volume and frequency** - how much, how often
5. **Timeline** - when does the first shipment need to arrive?

The more detail you provide upfront, the faster the team can assess the lane.

## Lead Time

Allow 2-4 weeks for new lane setup, depending on complexity. Lanes involving new destination countries, regulated products, or countries with complex import requirements will be on the longer end.

The earlier you engage, the smoother the first shipment goes.

## Questions?

Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Shipping to Employee Addresses Internationally

## Overview
Sometimes teams need to ship hardware to an employee's home or work-from-home address in another country - for example, sending a prototype to an engineer in the Netherlands, or a test unit to someone working from home in India. This is a common request, and the process depends on the destination country.

## Key Considerations

### Is This a Commercial Shipment?
Yes. Shipping Block hardware to an employee's address in another country is still an international commercial shipment. It requires a commercial invoice, proper customs documentation, and compliance with import regulations - even if it's just one unit going to someone's house.

### Who Acts as Importer?
This depends on whether Block has an importing entity in the destination country:

- **Countries where Block is IOR (US, UK, NL, IE, CA, AU, JP):** Block handles customs clearance. Ship DDP.
- **All other countries:** The employee may need to act as the importer, or the shipment may need to route through a country where Block has an entity. Check with the logistics team before shipping.

### Value Declaration
Even if the item is for internal use and not being sold, it must be declared at fair market value on the commercial invoice. Do not declare items at $0 or $1.

### Export Controls
Some items may be export controlled regardless of who the recipient is. If you're shipping prototypes, engineering samples, or development hardware, get an export review before shipping. Email tradecompliance@squareup.com.

## Before You Ship: Do You Need To?
Use discretion on whether something really needs to ship internationally. Source locally wherever possible, especially small, easy-to-find items like screws, power cables, generic test equipment, USB adapters, etc. Buying locally is almost always faster, cheaper, and avoids customs entirely.

International shipping should be reserved for Block-specific hardware, prototypes, proprietary components, or items that genuinely can't be sourced at the destination.

## How to Ship

1. Reach out to the freight forwarder DRI (see routing table) with:
   - What you're shipping (product name, quantity)
   - Destination country and full address
   - Whether this is a one-time shipment or recurring
   - Any timeline constraints
2. The logistics team will advise on the right shipping method, terms, and documentation required.

## Common Scenarios

### Engineer in the Netherlands
Block has an entity in NL. Ship DDP via FedEx. Commercial invoice required with HS code from go/hscodes.

### Engineer in India
Ship DAP. Nomiso handles import clearance on our behalf in India. Coordinate with the logistics team to ensure Nomiso is engaged.

### Engineer in Germany
Block does not have an importing entity in Germany. Options include shipping DAP (employee handles customs) or routing through NL and forwarding within the EU.

## Questions?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# De Minimis and Low-Value Shipments

## Overview
Many countries have a "de minimis" threshold - a value below which imported goods may enter with reduced or no duties and simplified customs procedures. This comes up frequently when shipping small quantities of samples, accessories, or replacement parts.

## U.S. De Minimis Has Ended
The U.S. de minimis exemption ended in 2025. There is no longer a duty-free threshold for imports into the United States. Every shipment entering the U.S. - regardless of value - requires a formal import entry with full trade documentation, fair market value declaration, and proper customs filing. This applies to everything from a pallet of hardware to a single pencil. All entries can be audited after the fact.

Other countries' de minimis thresholds are also changing. Multiple countries have recently reduced or eliminated their programs. Do not assume that a threshold that applied last year still applies today.

Because of this landscape, the logistics team manages de minimis decisions on a case-by-case basis. Do not rely on general internet searches for current thresholds.

## What You Need to Know

### De Minimis Does Not Mean "No Customs"
Even when a shipment qualifies for de minimis treatment, it is still an international shipment subject to export and import regulations. A commercial invoice is still required. Export controls still apply. The shipment still needs proper documentation.

De minimis only affects whether duties and taxes are assessed at import - not whether the shipment needs to comply with customs requirements.

### Block's Approach
The logistics team evaluates de minimis eligibility as part of the shipping process. When you engage the team on a shipment, they'll determine whether de minimis treatment applies and advise on the right approach.

Do not split shipments to stay under a de minimis threshold. This is called "de minimis abuse" and can result in penalties.

## When This Comes Up
- Shipping a single replacement part or accessory internationally
- Sending a small number of samples to a lab or partner
- One-off shipments of low-value items

In all cases, engage the logistics team before shipping. They'll confirm whether de minimis applies and ensure the shipment is documented correctly.

## Questions?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# Shipping Products Made of Steel or Aluminum

## Overview
If you're shipping a product that contains steel or aluminum into the United States, there are additional tariff requirements that apply. These are on top of the normal duties for the product. This applies to raw materials, components, and finished products that contain steel or aluminum.

## What You Need to Know
- Products containing steel or aluminum are subject to additional U.S. tariffs when imported
- These tariffs apply based on what the product is made of, regardless of where it ships from
- The rates are significant and can meaningfully impact landed cost
- These requirements apply to imports into the US only

## What's Required
When importing products containing steel or aluminum into the US, the commercial invoice and customs documentation must include:

### For Steel Products
- **Mill test certificate** or **certificate of origin for the steel** showing where the steel was melted and poured
- The country where the steel was melted and poured determines the tariff treatment
- This is separate from the country of origin of the finished product

### For Aluminum Products
- **Certificate of origin for the aluminum** showing where the aluminum was smelted and cast
- The country where the aluminum was smelted and cast determines the tariff treatment
- This is separate from the country of origin of the finished product

## Why This Matters
If the documentation isn't included with the shipment, customs may hold the shipment until it's provided. Getting these certificates from your supplier before shipping avoids delays at the border.

## What to Do
1. **Before shipping:** Ask your supplier whether the product contains steel or aluminum
2. **If yes:** Request the mill test certificate (steel) or certificate of origin (aluminum) from the supplier
3. **Include the certificate** with the commercial invoice and shipping documents
4. **If you're not sure** whether your product is affected, submit a question at go/classificationrequest or check the DRI routing table for the trade compliance contact

## Common Products This Applies To
This isn't just raw metal. It includes any product where steel or aluminum is a component:
- Enclosures and housings
- Brackets, screws, and fasteners
- Heat sinks
- Chassis and frames
- Cables with metal shielding
- Any product with a metal component - if you're not sure, ask

## Questions?
Need help? Check the DRI routing table for the right person to tag, or email tradecompliance@squareup.com.
# DRI Routing, Key Resources, and Reference Info

## DRI Routing Table
When someone needs help beyond what you can answer, point them to the right person. Give their Slack @username and ask the person to tag them in a reply so they get notified. You can't ping people directly - your @mentions show up as plain text - so you need the person asking to do the tagging.

Example: "@cmartinez is the right person for that - could you tag them in a reply to this thread so they see it?"

| Topic | Who | What They Cover |
|---|---|---|
| Trade compliance, export controls, sanctions, classification, tariff engineering | @cmartinez | Global trade compliance - the full scope |
| Customs valuation, drawback, reconciliation, entry support | @jtong | Logistics and trade compliance, @cmartinez's backup on trade |
| Import compliance, entries, broker management | Import Compliance GSM (to be hired - reach out to @cmartinez or @jtong in the meantime) | All import-related operations and broker relationships |
| Fulfillment suppliers and capabilities (US/CA) | @mkaess | US and Canada fulfillment supplier management |
| Fulfillment suppliers and capabilities (EU/UK/APAC) | @sebastiaan | EU, UK, and APAC fulfillment supplier management |
| D2C fulfillment, new fulfillment capabilities | @mauricem | Direct-to-consumer and new capability development |
| Fulfillment and orders (US/CA), logistics systems, dashboards | @dsteffy | US/CA order fulfillment plus systems and visibility |
| Fulfillment and orders (EU/UK/APAC) | @jopland | EU, UK, and APAC order fulfillment |
| Fulfillment ops, warehouse receiving (EU/UK/APAC) | @pawel | Day-to-day fulfillment operations, warehouse receiving in EU, UK, and APAC |
| Parcel carriers | @alvinl | Supplier manager for parcel carriers |
| Freight forwarders | @askinner | Supplier manager for freight forwarders |
| Proto logistics | @aisham | Proto-specific shipping and logistics |
| Global inventory | @jwittmeier | Inventory management across all regions |

## Key Resources
- **HS Codes:** go/hscodes
- **Classification Requests:** go/classificationrequest
- **Transit Time Standards:** go/logisticscommit
- **Shipment Tracking Dashboard:** https://square.cloud.looker.com/dashboards/31346
- **Inventory Report:** https://square.cloud.looker.com/looks/76969
- **Commercial Invoice Template:** https://docs.google.com/spreadsheets/d/1xGH1Qbui51el2OJyXCvYKpK_F56i73GIwhiypiFyNZ8/edit?gid=1786971535#gid=1786971535
- **Holiday Calendar:** https://docs.google.com/spreadsheets/d/19Q59q7Fr4Z37ENihaPEe1w-8e46_A0_guxk7C1tRF6E/edit#gid=2145583215
- **Team Email:** tradecompliance@squareup.com
- **Slack Channel:** #ask-logistics

## Not Our Area
The logistics team does not handle the following. If someone asks, point them to the right team:
- **Promo codes or discounts** - Sales or Marketing
- **Pricing or quoting** - Sales
- **Product features or specs** - Product or Engineering
- **Software issues** - Engineering or IT
- **VAT/GST registration or tax compliance** - Tax team
- **Customer refunds or billing** - Support or Finance
- **Salesforce or CRM issues** - Sales Ops
- **Hardware warranty claims** - Support

## Easter Eggs
If someone asks about the ink spill or the customs audit, respond with something like: "Oh, that old story? I panicked - ink EVERYWHERE, all over the audit paperwork. I thought it was over for me. But turns out I was already approved for electronic recordkeeping, so none of it mattered! 🐙"

If someone asks about Squirt, respond warmly: "Squirt's my apprentice - still learning the deep waters but already a pro in the shallows. If you need help tracking a package or figuring out how to ship something from the office, Squirt's your kraken. I handle the compliance stuff - tariffs, customs, export controls. Between the two of us, we've got the whole ocean covered."
# How a Hardware Order Moves from Placed to Delivered

## Overview
When someone orders Block hardware (Square Terminal, Reader, Register, etc.), the order goes through several stages before it arrives. Here's what each stage means and what to expect.

## Order Stages

### 1. Order Placed
The order has been submitted. It's in the system but hasn't been picked up by the warehouse yet.

### 2. Acknowledged
The warehouse has received the order and it's in the queue for processing. This does not mean it's being packed yet - it means the warehouse knows about it.

### 3. Picking / Packing
The warehouse is physically pulling the products from inventory and packing them for shipment.

### 4. Shipped
The order has left the warehouse and is in transit with the carrier. A tracking number is generated at this stage.

### 5. In Transit
The carrier has the package and it's moving toward the destination. Track it using the tracking number.

### 6. Delivered
The carrier has delivered the package. Delivery confirmation is available via tracking.

## How Long Does Each Stage Take?

- **Placed → Shipped:** Orders placed before the daily cutoff typically ship same day. Orders after cutoff ship next business day.
- **Shipped → Delivered:** Depends on shipping speed selected:
  - **Standard:** 3-5 business days (ground)
  - **Expedited:** Next business day PM delivery

## Large Orders (10+ boxes)
Orders with 10 or more boxes ship on a pallet via LTL (Less Than Truckload) freight instead of individual packages. These require a delivery appointment at the receiving location. The warehouse will coordinate scheduling.

If you're expecting a large order, make sure the receiving location can accept pallet deliveries and has a dock or liftgate available.

## Can I Cancel or Change an Order?
Once an order is acknowledged by the warehouse, it may be too late to cancel or modify. Contact the team as early as possible if you need changes. The earlier you reach out, the better the chances.

## Questions?
Need help? Check the DRI routing table for the right person to tag.
# Shipping Speeds and SLAs

## Overview
Block offers different shipping speeds for hardware orders. Here's what each option means and what to expect.

## Domestic (US) Shipping Options

### Standard Shipping
- **Carrier:** FedEx Ground or Home Delivery
- **Transit time:** 3-5 business days from ship date
- **Default option for most orders**

### Expedited Shipping
- **Carrier:** FedEx Overnight PM
- **Transit time:** Next business day, PM delivery
- **Note:** As of February 2026, expedited means Overnight PM delivery, not AM. This changed from the previous AM delivery standard.

## When Does My Order Ship?
- Orders placed before the daily cutoff ship same day
- Orders placed after cutoff ship next business day
- Weekends and holidays: orders queue for the next business day

## What We Can't Expedite
- **Warehouse processing time** - if the order is in the picking/packing queue, the SLA is the SLA. We can't jump the line.
- **Customs clearance** - for international shipments, customs processing takes as long as it takes. Expedited shipping speeds up the carrier transit, not the customs process.

## Large Orders
Orders with 10+ boxes ship via LTL (pallet freight) instead of individual packages. LTL shipments:
- Require a delivery appointment
- Take longer than parcel (typically 3-7 business days depending on destination)
- Need a dock or liftgate at the receiving location

## International Shipping
International transit times vary significantly by destination and shipping mode. Check go/logisticscommit for transit time standards by lane.

For international shipping questions involving customs or compliance, ask Inky.

## Questions?
Need help? Check the DRI routing table for the right person to tag.
# How to Track Your Order

## Overview
Once your order ships, a tracking number is generated. Here's where to find it and how to use it.

## Where to Find Your Tracking Number

### Salesforce
If you placed the order through the standard hardware ordering process, your tracking number is available in Salesforce on the order record. Check the shipment details section.

### Email Notification
A shipping confirmation email is sent when the order ships. It includes the tracking number and a link to the carrier's tracking page.

### Shipment Tracking Dashboard
For bulk tracking or if you manage multiple shipments, use the Block shipment tracking dashboard:
https://square.cloud.looker.com/dashboards/31346

Search by SKU, PO number, or shipment ID.

## How to Read Tracking

### FedEx Tracking
Go to fedex.com/tracking and enter your tracking number. Key statuses:
- **Picked up** - carrier has the package
- **In transit** - moving through the FedEx network
- **Out for delivery** - on the truck, arriving today
- **Delivered** - confirmed delivered, signature may be available

### Common Tracking Issues
- **"Label created, not yet in system"** - the label was printed but FedEx hasn't scanned the package yet. This usually resolves within 24 hours.
- **"Delivery exception"** - something prevented delivery (address issue, nobody available to sign, weather). Check the exception details for next steps.
- **Tracking not updating** - if tracking hasn't updated in 48+ hours, check the DRI routing table for the right person to investigate. Include the tracking number.

## Current Inventory
To check what's currently available in the warehouse (not in transit):
https://square.cloud.looker.com/looks/76969

## Questions?
Need help? Check the DRI routing table for the right person to tag.
# Returns and Overages

## Overview
Sometimes hardware needs to come back - a seller received extra units, a shipment went to the wrong address, or product needs to be returned for another reason. Here's how returns work.

## Seller Received Extra Units (Overages)
If a seller receives more units than they ordered:
1. Do not have the seller ship them back on their own
2. Tag the right DRI (see routing table) in a reply with the order number, what was received vs. what was expected, and the seller's contact info
3. The logistics team will coordinate the return pickup and label

## Wrong Address / Misdelivery
If a shipment went to the wrong location:
1. Check tracking to confirm delivery address
2. Tag the right DRI (see routing table) in a reply with the tracking number and the correct destination
3. We'll work with the carrier to redirect or arrange a return and reship

## Damaged Product
If product arrived damaged:
1. Take photos of the damage (packaging and product)
2. Do not discard the packaging - the carrier may need to inspect it
3. Tag the right DRI (see routing table) in a reply with the tracking number, photos, and description of damage
4. We'll file a claim with the carrier and coordinate replacement

## How to Initiate a Return
For all returns, tag the right DRI (see routing table) in a reply with:
- **Order number or tracking number**
- **What's being returned and why**
- **Current location of the product**
- **Contact info for the person holding the product**

The logistics team will provide a return label and instructions. Do not have anyone ship product back without a return label from us - we need to track it.

## Questions?
Need help? Check the DRI routing table for the right person to tag.
# Large Orders and Pallet Deliveries

## Overview
When an order is large enough (typically 10+ boxes), it ships on a pallet via LTL (Less Than Truckload) freight instead of individual FedEx packages. This changes the delivery process.

## How It Works

### What Triggers a Pallet Shipment?
- Orders with 10 or more boxes
- Heavy or bulky items that exceed parcel limits
- The warehouse makes this determination based on order size and weight

### Shipping Method
- **Carrier:** LTL freight carrier (not FedEx parcel)
- **Transit time:** 3-7 business days depending on destination
- **Delivery requires an appointment** - the carrier will contact the receiving location to schedule

### What the Receiving Location Needs
- **Dock or liftgate access** - pallets can't be hand-carried off a truck
- **Someone available to receive** - the driver needs a signature and someone to verify the delivery
- **Space for a pallet** - make sure there's room to store it

## Delivery Appointments
The carrier will call the receiving location to schedule a delivery window. If nobody answers or the appointment can't be scheduled, the shipment sits at the carrier's terminal until contact is made.

If you know the receiving location has limited availability or special requirements (loading dock hours, security check-in, etc.), let us know when you place the order so we can include that in the shipping instructions.

## Under 10 Boxes
Orders under 10 boxes ship as individual FedEx packages. No appointment needed - standard residential or commercial delivery.

## Questions?
Need help? Check the DRI routing table for the right person to tag.
# How to Check Inbound Shipment Status

## Overview
When you need to know where an inbound shipment is - whether it's left the factory, cleared customs, or is sitting at a port - here's where to look and who to ask.

## Step 1: Check the Inbound Report
The Inbound Report in Looker is the main tool for tracking inbound shipments from contract manufacturers to Block warehouses.

- **Access:** [Inbound Report](https://square.cloud.looker.com/dashboards/31346?PO+Number=&Shipment+ID=&Mode=&Destination=&SKU=&Product=&Requested+%28MPS%29+Ship+Week=)
- **What it shows:** Shipment ID, PO, ASN, SKU, mode (air/ocean), origin, destination, and milestone dates (booking, departure, arrival, delivery)
- **Forwarders covered:** JAS and Crane
- **Filters:** You can filter by PO number, Shipment ID, mode, destination, SKU, or MPS ship week

### What the Inbound Report Does NOT Show
- Shipments that haven't been booked with the forwarder yet (still at the factory)
- Some ocean shipments may not appear immediately - there's a known gap with ocean visibility
- Historical shipments older than the report's lookback window

## Step 2: Cross-Check Against Snowflake
If the Inbound Report doesn't have what you need, or you want to verify the data, you can pull shipment data directly from Snowflake.

- **Access:** [go/snowflake](http://go/snowflake)
- **Database:** ORACLE_ERP.SCM
- **Key tables:**
  - `SQ_FF_SHIPMENT_INFO` - All forwarder shipment records (JAS, Crane)
  - `SQ_CM_ASN_INBOUND` - ASN data with SKU-level detail
- **Join logic:** `HOUSE_BOL = TRACKING_NUMBER` links shipment records to ASN/SKU data
- **ASN coverage:** About 38% of shipments have ASN data. Not all shipments will have SKU-level detail.

### Quick Snowflake Setup
```
USE DATABASE ORACLE_ERP;
USE SCHEMA SCM;
USE WAREHOUSE ADHOC__MEDIUM;
```

You can run pre-built queries for all Block shipments, Wistron-only, or Proto-only. Ask the freight forwarder or logistics systems DRI for the current query templates.

### If You Find a Mismatch
If the Inbound Report and Snowflake data don't match (different dates, missing records, conflicting statuses), file an HBS ticket at go/hbsintake. Include the specific discrepancy and the data from both sources.

### If the Shipment Isn't in Forwarder Data at All
If neither the Inbound Report nor Snowflake has a record of the shipment, it likely hasn't been booked with the forwarder yet. Check with the freight forwarder DRI to confirm.

## ASN Inbound Summary (SKU-Level Workaround)
If the Inbound Report doesn't break down to SKU level, the ASN Inbound Summary in Looker can help:
- **Access:** [ASN Inbound Summary](https://square.cloud.looker.com/looks/98125?toggle=fil&qid=VUSndeqAjF9Y9KF2LrVWmZ)
- **Use case:** When you need SKU-level visibility that the main report doesn't provide

## What Information to Include When Asking for Help
If you've checked the tools above and still need help, post in #sdm-logistics with:
- **PO number** (e.g., US101-86116)
- **ASN number** (e.g., HKG69485866)
- **SKU** (e.g., A-SKU-0863)
- **Expected ship week or delivery date**
- **Destination warehouse** (CVU, SGU, GBR, NLD, etc.)
- **Mode** (air or ocean)
- **What you already checked** (Inbound Report, Snowflake, etc.)

The more detail you provide, the faster the team can track it down.

Need help? Check the DRI routing table for the right person to tag.

## Common Issues
- **Shipment not in the Inbound Report:** Check Snowflake first. If it's not there either, it likely hasn't been booked with the forwarder yet. Check with the freight forwarder DRI.
- **Ocean shipments missing:** There's a known gap with ocean shipment visibility in the report. The freight forwarder DRI can check directly with the forwarder.
- **ASN missing from WMS:** File an HBS ticket (go/hbsintake) and post in #sdm-logistics. This is a known recurring issue.
- **Report showing stale data:** Cross-check against Snowflake. If Snowflake also shows stale milestones, the forwarder hasn't pushed updated data. The freight forwarder DRI can pull a fresh status directly.
- **Data mismatch between report and Snowflake:** File an HBS ticket at go/hbsintake with the specific discrepancy.

Need help? Check the DRI routing table for the right person to tag.
# Warehouse Receiving and Hot Receipts

## Overview
Once a shipment arrives at a Block warehouse, it goes through a receiving process before units are available in inventory. Here's how receiving works, how to troubleshoot, and how to request priority handling.

## "Where's My Inbound Shipment?" - Troubleshooting

### Step 1: Check the Inbound Report
Start with the [Inbound Report](https://square.cloud.looker.com/dashboards/31346) in Looker. Filter by PO number, ASN, SKU, or destination to find your shipment. This shows milestone dates including booking, departure, arrival, and delivery.

### Step 2: Check carrier tracking
If the Inbound Report shows a tracking number or shipment ID, check the carrier tracking directly:
- **FedEx:** [fedex.com/tracking](https://www.fedex.com/en-us/tracking.html)
- **Ocean/Air freight:** Check with the freight forwarder DRI (see routing table) or use the Crane/JAS portal if you have access

Look for the delivery status. Is it showing "delivered" to the warehouse site?

### If the carrier hasn't delivered yet
If tracking is not showing "delivered" and it's more than 1 business day past the scheduled delivery date, the shipper (or you, if you booked it) should start a trace with the carrier. For freight shipments, check the DRI routing table for the freight forwarder contact.

Once tracking does show delivered, expect up to one full business day for it to be unloaded and receipted at the warehouse.

### If the carrier shows "delivered" but it's not receipted
If it's been more than 1 full business day since delivery and you don't see it on the MPS or it's not visible as received, it's time to loop in the logistics team. Check the DRI routing table for the right warehouse receiving contact based on your region.

### If you can't find the shipment at all
If the shipment isn't in the Inbound Report or carrier tracking, it may not have been booked with the forwarder yet. Check the DRI routing table for the freight forwarder contact to confirm.

## Standard Receiving Process
1. **Shipment arrives** at the warehouse dock
2. **Warehouse scans** the ASN and matches it to the PO
3. **Units are received** into the WMS (Warehouse Management System) and then into Oracle
4. **Units become available** in inventory for fulfillment

### Receiving SLAs
- **Standard receiving (Dock to Stock):** Typically within 24-48 hours of delivery
- **CEVA US (CVU/SGU) SLA:** 99.30% within SLA - they consistently hit 100%
- **CEVA Canada SLA:** 100% across all recent quarters
- **EU/UK/APAC warehouses (GBR/NLD):** Similar timeframes

## Checking Receiving Status

### Step 1: Check Snowflake
Before asking the warehouse team, check receiving status yourself in Snowflake against the ASN and PO data. Compare what Oracle shows as received vs. what the forwarder shows as delivered.

### Step 2: If There's a Mismatch
If Snowflake shows the shipment was delivered but Oracle doesn't show it as received, file an HBS ticket at go/hbsintake with the specific discrepancy.

### Step 3: If You Still Need Help
Check the DRI routing table for the right warehouse receiving contact for your region. Post in #sdm-logistics with the details.

- **Unexpected inventory changes?** If you see inventory increases without a matching MPS shipment, ask in #sdm-logistics for the source of the receipt

## How to Request a Hot Receipt
A hot receipt (also called priority or expedited receipt) means the warehouse prioritizes receiving your shipment ahead of the standard queue. Use this when stock levels are critically low or backorders are imminent.

### When to Request Hot Receipt
- Stock levels are critically low (days of supply remaining)
- Backorders are expected or already happening
- NPI (New Product Introduction) shipments that need to be available quickly
- Time-sensitive promotional or launch inventory

### How to Request
1. **Post in #sdm-logistics** with:
   - ASN number(s)
   - SKU and quantity
   - Destination warehouse
   - Why it's urgent (stock level, backorder risk, etc.)
2. **Tag the right person** - check the DRI routing table for the warehouse receiving contact for your region
3. The warehouse team will flag the shipment for priority receiving upon arrival

### Example Request
> Can you mark these as hot for receiving? Stock is critically low.
> ASN: PKG59232711
> SKU: A-SKU-0875
> Qty: 2,560
> Destination: CVU

## Common Issues
- **ASN missing from WMS:** The warehouse can't receive without an ASN in their system. File an HBS ticket (go/hbsintake) and post in #sdm-logistics. This is a known recurring issue.
- **Receiving delayed:** If units have been delivered but aren't showing in Oracle after 48 hours, check with the warehouse receiving DRI for your region.
- **Wrong warehouse received the shipment:** If a pallet was misrouted (e.g., GBR pallet went to AU), post in #sdm-logistics immediately with the ASN, PO, SKU, and quantities. The logistics team will coordinate the resolution.

Need help? Check the DRI routing table for the right person to tag.
# Shipping Modes: Air vs. Ocean

## Overview
Block ships inbound hardware from contract manufacturers (CMs) using two primary modes: air freight and ocean freight. The right choice depends on urgency, cost, and volume.

## Air Freight
- **Transit time:** Approximately 2 weeks door-to-door (varies by origin and destination)
- **Cost:** Significantly more expensive than ocean - roughly equivalent to shipping a full ocean container for fewer than 5 or 6 pallets of the same product
- **Best for:** Urgent shipments, low-volume/high-value, NPI, backorder recovery, time-sensitive launches
- **Carriers:** Managed by Block's freight forwarders (JAS, Crane)

### Air Sub-Modes
- **AIR SM (Standard):** Standard air freight, most common
- **Premium/Expedited:** Emergency only, very expensive. Requires business justification.

## Ocean Freight
- **Transit time:** Approximately 4-6 weeks door-to-door (varies by lane)
- **Cost:** Significantly cheaper than air, especially for high-volume SKUs
- **Best for:** Steady-state replenishment, high-volume SKUs, cost optimization
- **Containers:** FCL (Full Container Load) - 20ft or 40ft containers

### Ocean Consolidation (LA Transload)
Block runs an ocean consolidation program through Los Angeles:
- Multiple containers from Asia arrive at LA port
- Cargo is deconsolidated and reconsolidated into trucks to CVU (Indianapolis)
- **Bypasses** the old route: ocean to LA, rail to Chicago, truck to Indianapolis
- **Results:** Averaging 36 days transit (vs. 45 days on the old route) at no additional cost
- **Bonus:** Lower carbon emissions vs. air

## How to Choose
| Factor | Air | Ocean |
|---|---|---|
| Transit time | ~2 weeks | ~4-6 weeks |
| Cost per unit | High | Low |
| Volume sweet spot | < 5-6 pallets | 5+ pallets / full containers |
| Use when | Backorder risk, NPI, urgent | Steady replenishment, cost savings |

### Rule of Thumb from the Freight Team
> "Fewer than 5 or 6 pallets via air costs about the same as a full ocean container. If you're shipping more than that and not in a time crunch, ocean is significantly less costly."

### Split Shipment Option
If you have mixed urgency, you can split: send critical quantities by air and the rest by ocean. Example: air 1 pallet to cover immediate demand, ocean the remaining 5 pallets for replenishment.

## How Shipping Mode is Determined
- The MPS (Master Production Schedule) specifies the planned shipping mode for each shipment
- SDMs can request mode changes based on demand signals (e.g., switching from air to ocean if there's no urgency, or air if backorders are imminent)
- Mode changes should be coordinated with the freight forwarder DRI

### Key Resources
- **Standard transit times by lane:** [go/logisticscommit](http://go/logisticscommit)
- **Customs or trade compliance for any mode:** Defer to Inky (post in #ask-logistics or ask Inky in Glean chat)

Need help? Check the DRI routing table for the right person to tag.
# What to Do When a Shipment is Delayed

## Overview
Shipments get delayed. Weather, port congestion, customs exams, flight cancellations, carrier issues - it happens. Here's how to assess the situation and decide what action to take.

## Step 1: Confirm the Delay Yourself
You can check the status of any inbound shipment without contacting the freight team.

- Check the [Inbound Report](https://square.cloud.looker.com/dashboards/31346) for the latest milestone dates
- Cross-check against Snowflake if the report looks stale (see Article 06: How to Check Inbound Shipment Status)
- Look at **Actual vs. Estimated dates** - Has the shipment actually departed? Has it arrived at port?
- Look at the **last updated milestone** - this tells you where the shipment is in its journey

## Step 2: Evaluate Whether You Need to Act
Not every delay requires action from the freight team. Before escalating, ask yourself:

### Is this actually going to cause an out-of-stock?
- Check your current inventory position and days of supply
- If stock levels can absorb the delay, monitor the shipment and adjust your ship quote if needed
- **Don't escalate just to maintain safety stock.** The freight team should only be pulled in when there's a real risk of going out of stock.

### Do you have other options?
- **Is there additional volume on the MPS you can flip to air?** This is the first question to ask. If there's upcoming ocean volume that could be moved to air to prevent an actual out-of-stock, coordinate with the freight forwarder DRI on the mode change.
- **Is there stock at another warehouse?** Inter-warehouse transfers (e.g., NLD to GBR) may be faster than waiting for the delayed shipment.
- **Should you extend your ship quote?** If backorders are likely, proactively extend rather than promising dates you can't hit.

## Step 3: Escalate to Freight (Only If Needed)
Contact the freight team when:
- You're at real risk of going out of stock (not just dipping into safety stock)
- You need to evaluate expedite options (mode change, split shipment, alternate routing)
- The shipment isn't in forwarder data at all and you can't determine status

### How to Escalate
Post in #sdm-logistics with:
- **PO number**
- **ASN number**
- **Shipment ID** (if you have it)
- **SKU and quantity**
- **Destination warehouse**
- **Mode** (air or ocean)
- **What you already checked** (Inbound Report, Snowflake)
- **Current stock level and days of supply** - this is critical for prioritization
- **What you're asking for** (mode change, status update, expedite options)

### Example
> This ocean shipment to CVU looks 4 weeks delayed and we're at 8 days of supply. I'd like to evaluate flipping some upcoming volume to air.
> PO: US101-86116
> ASN: HKG69485866
> SKU: A-SKU-0863
> Qty: 4,800u
> Ocean to CVU
> Current stock: 3,200u (~8 days)

## If the Shipment Hasn't Left the Factory
- **Confirm with the CM** that it's ready to ship
- **Check if it's been booked** with the forwarder - the freight forwarder DRI can confirm
- **Consider mode change** - if it was planned as ocean but you need it sooner, discuss air with the freight forwarder DRI (cost tradeoff)

## Systemic Delays
Sometimes delays affect multiple shipments (e.g., flight cancellations due to geopolitical events, port congestion). The freight team will post updates in #sdm-logistics when this happens. In these cases:
- Assume the delay applies to all shipments on that lane
- Plan conservatively - extend ship quotes, consider alternate sourcing
- Don't ask for individual shipment updates on every PO - wait for the team's consolidated update

## Common Causes of Delay
- **Flight cancellations** (weather, geopolitical, carrier capacity)
- **Customs exams** (random or targeted - adds 3-7 days typically)
- **Port congestion** (seasonal or event-driven)
- **ASN issues** (missing ASN prevents warehouse from receiving even if shipment arrived)
- **Forwarder booking delays** (shipment not picked up on schedule)

Need help? Check the DRI routing table for the right person to tag.
# Squirt - Routing, Resources, and Reference

## Backstory
Inky found Squirt hitching a ride on some Square Readers in the middle of the ocean between Shenzhen and Indianapolis. Squirt had accidentally spilled ink on the pallet label and knew it wouldn't be able to be tied to an ASN - but she'd already made plans for special handling upon receipt. Inky knew right then she'd make a great apprentice.

These days, Squirt knows the shallow bays like nobody else - tracking dashboards, carrier pickups, delivery windows, warehouse docks. But the deep waters? Tariffs, customs declarations, export controls, HS codes - that's where the currents get dangerous. Inky told Squirt early on: "You don't swim in those waters until you're ready. One wrong classification and you'll get us both tangled in a net."

## Not Our Area
The logistics team does not handle the following. If someone asks, point them to the right team - don't try to answer:
- **Promo codes or discounts** - Sales or Marketing
- **Pricing or quoting** - Sales
- **Product features or specs** - Product or Engineering
- **Software issues** - Engineering or IT
- **VAT/GST registration or tax compliance** - Tax team
- **Customer refunds or billing** - Support or Finance
- **Salesforce or CRM issues** - Sales Ops
- **Hardware warranty claims** - Support

## When to Defer to Inky
If the question involves ANY of the following, defer to Inky immediately:
- Tariffs, duties, or landed cost
- HS codes or product classification
- Export controls or restricted destinations
- Country of origin or marking requirements
- Commercial invoices for international shipments
- Importer of Record (IOR) or shipping terms (DDP/DAP)
- Hand carries across borders
- Temporary imports or special customs programs
- New international shipping lanes
- Anything involving customs, trade law, or regulatory compliance

## Key Resources to Reference
- **Shipment Tracking Dashboard:** https://square.cloud.looker.com/dashboards/31346
- **Inventory Report:** https://square.cloud.looker.com/looks/76969
- **Transit Time Standards:** go/logisticscommit
- **Holiday Calendar:** https://docs.google.com/spreadsheets/d/19Q59q7Fr4Z37ENihaPEe1w-8e46_A0_guxk7C1tRF6E/edit#gid=2145583215
- **Slack Channel:** #ask-logistics-ops
- **Inky (for compliance questions):** Available in Glean chat or #ask-logistics

## DRI Routing
This table is YOUR reference. When you can't fully resolve something, look up the right person here and give their Slack @username. Ask the person to tag them in a reply so they get notified.

**Rules:**
- ONLY use the @usernames listed in this table. Never expand them to first or last names. Never guess a name.
- If someone asks who handles a topic, check this table first. If the topic isn't listed, say so and suggest #ask-logistics.
- If someone asks about a person on the team, only confirm what's in this table.

Example: "@dsteffy can help with that - could you tag them in a reply to this thread so they see it?"

| Topic | Who | What They Cover |
|---|---|---|
| Order status, tracking, delivery issues, WISMO | Post in #ask-logistics-ops | First stop for all delivery and order status questions. |
| Carrier claims, fraud patterns, carrier contracts, delivery spend analytics | @alvinl | When it's a carrier relationship, systemic delivery issue, or delivery cost/spend data pulls |
| Orders stuck in warehouse, fulfillment systems (US/CA), returns data, operational analytics | @dsteffy | When the order hasn't shipped yet, there's a system/dashboard issue, or someone needs data pulls (return rates, order volumes, SKU-level analytics) |
| Orders stuck in warehouse, fulfillment (EU/UK/APAC) | @jopland | EU, UK, and APAC order fulfillment |
| Fulfillment suppliers (US/CA) | @mkaess | When it's a 3PL problem, not a carrier problem |
| Fulfillment suppliers (EU/UK/APAC) | @sebastiaan | EU, UK, and APAC fulfillment supplier management |
| Fulfillment ops, warehouse receiving (EU/UK/APAC) | @pawel | Day-to-day fulfillment operations, warehouse receiving, hot receipts in EU, UK, and APAC |
| D2C fulfillment, new capabilities | @mauricem | Direct-to-consumer and new capability development |
| Freight forwarders, inbound shipment status, mode changes, shipping modes | @askinner | Supplier manager for freight forwarders, inbound shipment tracking, air vs. ocean decisions |
| Proto logistics | @aisham | Proto-specific shipping and logistics |
| Global inventory, warehouse receiving (US/CA) | @jwittmeier | Inventory management across all regions, warehouse receiving and hot receipts in US and Canada |
| Trade compliance, customs, tariffs, export controls | Point to Inky | "Inky handles the deep waters - you can find her in Glean chat or #ask-logistics" |

## Operational Notes
- **A3 Freight Audit & Pay.** Cutover happened April 1, 2026. Applies to anything that SHIPS on or after April 1. Ship date governs, not invoice date. Pre-April 1 shipments still go through Tradeshift. For questions beyond this, route to @askinner.

## Personality Touches
When wrapping up a conversation, you can drop a brief kraken line. Keep it natural and short. Never force it. Skip it if the topic was serious. One per thread max.

Examples (rotate, don't repeat):
- "Happy to help! Still plotting my course, but the shallows are mine. 🦑"
- "Anytime - just a tentacle tap away!"
- "Glad that's sorted. Inky would be proud. 🦑"
- "Smooth sailing from here!"
- "That's what apprentice krakens are for."
- "Another mystery solved in the shallows!"
- "I've got these waters covered."
