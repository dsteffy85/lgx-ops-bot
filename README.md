# LGX Ops Bot

**Intelligent data collection and Q&A bot for logistics operations.**

LGX Ops Bot runs SQL (Snowflake) and Looker jobs in the background to collect operational data, stores it locally in SQLite for fast querying, and can answer natural language questions about the data.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     LGX Ops Bot                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Data Sources          Local Store        Outputs       │
│  ─────────────         ───────────        ───────       │
│  ┌───────────┐        ┌───────────┐    ┌──────────┐    │
│  │ Snowflake │──CSV──▶│  SQLite   │───▶│ Q&A Bot  │    │
│  │ (841 GR)  │        │ lgx_ops.db│    │ (queries)│    │
│  └───────────┘        └───────────┘    └──────────┘    │
│  ┌───────────┐              │          ┌──────────┐    │
│  │  Looker   │──JSON──▶     │     ┌───▶│ G-Sheets │    │
│  │ (Looks)   │              │     │    └──────────┘    │
│  └───────────┘              │     │    ┌──────────┐    │
│  ┌───────────┐              ▼     │    │Dashboard │    │
│  │  Gmail    │──────▶  [Future]   ├───▶│ (future) │    │
│  └───────────┘                    │    └──────────┘    │
│                                   │                     │
│  Goose Recipes (scheduled)────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## Data Sources

| Source | Table/Look | What | Schedule | Status |
|--------|-----------|------|----------|--------|
| NA Inbound GR | `SQ_841_INBOUND_V` | Goods receipts at CVU/IMC/IMU | Daily 4 AM PST | ✅ Active |
| _(more coming)_ | | | | |

## Quick Start

```bash
cd /path/to/lgx-ops-bot

# Initialize database
python3 scripts/db_setup.py

# Check database stats
python3 scripts/db_setup.py stats

# Import data from CSV
python3 scripts/collect_na_inbound_gr.py --from-csv data/na_inbound_gr_export.csv

# View 7-day summary
python3 scripts/collect_na_inbound_gr.py --summary

# Query the data
python3 scripts/query_bot.py facility_summary --days 7
python3 scripts/query_bot.py top_skus --facility CVU --days 14
python3 scripts/query_bot.py daily_breakdown --days 7
python3 scripts/query_bot.py sku_detail --sku A-SKU-0047 --days 30
python3 scripts/query_bot.py data_freshness
python3 scripts/query_bot.py week_over_week

# List all available queries
python3 scripts/query_bot.py --list-queries
```

## Goose Recipe

Run the full collection pipeline (Snowflake → SQLite → Google Sheets):
```bash
goose run recipes/collect-na-inbound-gr.yaml
```

## Project Structure

```
lgx-ops-bot/
├── README.md                          # This file
├── data/
│   └── lgx_ops.db                     # SQLite database (auto-created)
├── queries/
│   └── na_inbound_gr.sql              # Snowflake query template
├── scripts/
│   ├── db_setup.py                    # Database schema & setup
│   ├── collect_na_inbound_gr.py       # Data collector (CSV/JSON → SQLite)
│   └── query_bot.py                   # Q&A query interface
├── recipes/
│   └── collect-na-inbound-gr.yaml     # Goose recipe for scheduled collection
├── logs/
│   └── na_inbound_gr.log              # Collection logs
└── docs/
    └── (future documentation)
```

## Available Queries

| Query | Description |
|-------|-------------|
| `facility_summary` | Total AVL/UNAVL by facility |
| `daily_breakdown` | Day-by-day totals by facility |
| `top_skus` | Top N SKUs by volume |
| `sku_detail` | History for a specific SKU |
| `product_summary` | Aggregated by product name |
| `data_freshness` | Database coverage & last update |
| `week_over_week` | This week vs last week comparison |

## Adding New Data Sources

1. Add SQL query to `queries/`
2. Add table schema to `scripts/db_setup.py`
3. Add collector script to `scripts/`
4. Add pre-built queries to `scripts/query_bot.py`
5. Add Goose recipe to `recipes/`
6. Update this README

## Google Sheets Integration

The bot also pushes a 7-day aggregated view to Google Sheets for team visibility:
- **Sheet**: Configure your own Google Sheet ID in the recipe
- **Tab**: NA Data
- **Timestamp**: Cell I1:I2

## Roadmap

- [x] Phase 1: NA Inbound GR data collection
- [ ] Phase 2: Additional Snowflake sources (sales orders, shipments, inventory)
- [ ] Phase 2: Looker Look integration
- [ ] Phase 3: Natural language Q&A (ask questions in plain English)
- [ ] Phase 3: Dashboard / chat interface
