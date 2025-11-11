# Schema Documentation

This directory contains detailed schema documentation for all tables in the OmicIDX data warehouse.

## Organization

Schemas are organized by layer:
- `bronze/` - Staging tables
- `geometadb/` - GEOmetadb compatibility views
- `marts/` - Analytics-ready tables (if available)

## Schema Files

Schema documentation files will be generated or manually created here. Each schema file should include:
- Complete column list with types
- Column descriptions
- Example queries
- Relationships to other tables

## Auto-Generation

Schema documentation can be auto-generated from the `catalog.json` file when the warehouse is deployed.

