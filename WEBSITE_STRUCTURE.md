# Website Structure Proposal

## Project Context

**Primary Deliverable**: The data warehouse itself (frozen data lake in parquet format on R2/S3), not the ETL software.

**Website Purpose**: Public-facing data catalog and documentation site that helps users:
- Discover what data is available in the warehouse
- Understand schemas and data structures
- Learn how to access the data (remote DuckDB, direct parquet queries)
- See example queries and use cases
- Understand data sources, provenance, and update frequency

The ETL code documentation is secondary - more "how we built this" for transparency, rather than "how to use this software."

## Recommended Approach: Monorepo with Dedicated `docs/` Directory

Given your preference for consolidating code for AI agents and the existing project structure, I recommend a **monorepo approach** with a dedicated documentation/website directory focused on the **data product**.

## Proposed Directory Structure

```
omicidx-gh-etl/
├── omicidx_etl/          # ETL code (secondary - "how we built it")
├── sqlmesh/              # SQLMesh models (secondary - technical reference)
├── docs/                 # NEW: Public-facing DATA CATALOG site
│   ├── _quarto.yml       # Quarto configuration
│   ├── index.qmd         # Homepage: "What data is available?"
│   ├── getting-started/
│   │   ├── access.qmd           # How to access the data lake
│   │   ├── remote-database.qmd  # Using remote DuckDB
│   │   ├── direct-parquet.qmd   # Querying parquet directly
│   │   └── examples/
│   │       ├── first-query.ipynb
│   │       └── data-exploration.ipynb
│   ├── data-catalog/     # PRIMARY CONTENT
│   │   ├── overview.qmd
│   │   ├── sra/
│   │   │   ├── index.qmd        # SRA data overview
│   │   │   ├── schema.qmd       # Table schemas
│   │   │   ├── examples.ipynb   # Query examples
│   │   │   └── access-patterns.qmd
│   │   ├── geo/
│   │   │   ├── index.qmd
│   │   │   ├── schema.qmd
│   │   │   └── examples.ipynb
│   │   ├── biosample/
│   │   │   └── ...
│   │   └── catalog.json         # Auto-generated from deployment
│   ├── schemas/          # Detailed schema documentation
│   │   ├── bronze/
│   │   ├── geometadb/
│   │   └── marts/
│   ├── examples/        # Interactive query notebooks
│   │   ├── common-queries.ipynb
│   │   ├── joins-across-datasets.ipynb
│   │   └── visualizations.ipynb
│   ├── about/            # Secondary: how we built it
│   │   ├── data-sources.qmd     # Source data info
│   │   ├── etl-process.qmd      # ETL overview (brief)
│   │   └── architecture.qmd     # Warehouse architecture
│   └── _site/            # Generated site (gitignored)
├── .github/
│   └── workflows/
│       └── deploy-docs.yml
├── README.md             # Existing (unchanged)
└── ... (other existing files)
```

## Why This Structure?

### Advantages

1. **AI Agent Friendly**: All code and docs in one repo = full context
2. **Easy Cross-References**: Docs can link to actual code files
3. **Single Source of Truth**: Documentation lives next to code
4. **Simplified CI/CD**: One repo, one pipeline
5. **Version Alignment**: Docs version with code automatically

### Separation of Concerns

- **`docs/`**: **Data catalog** - Public-facing documentation about the data warehouse
  - Focus: "What data is available and how do I use it?"
  - Primary audience: Data consumers/researchers
  - Content: Schemas, access patterns, query examples, data catalog
- **`sqlmesh/README.md`**: Technical reference for developers/maintainers
- **`README.md`**: Project overview (ETL software)
- **`about/` in docs**: Brief "how we built it" for transparency (secondary)

## Static Site Generator Options

### Option 1: Quarto (⭐ Recommended for Data Science)

**Why Quarto is Perfect for Your Project**:
- **Native Notebook Support**: Renders Jupyter notebooks directly (`.ipynb` files)
- **Code Execution**: Can execute Python code during build (or show cached results)
- **SQL Syntax Highlighting**: Excellent SQL support with query result display
- **Interactive Elements**: Supports interactive plots, tables, and widgets
- **Multi-Format Output**: HTML, PDF, Word, presentations
- **Python-First**: Works seamlessly with your Python stack
- **Data Science Focus**: Built specifically for technical/scientific documentation
- **Beautiful Defaults**: Modern, clean design out of the box

**Notebook Integration**:
- Include `.ipynb` files directly in docs
- Convert notebooks to documentation pages
- Execute notebooks during build (or use cached outputs)
- Show code + outputs side-by-side
- Interactive widgets (Plotly, Bokeh, etc.)

**Setup**:
```bash
# Install Quarto (separate binary, not Python package)
# https://quarto.org/docs/get-started/

# Initialize project
cd docs
quarto create-project . --type website

# Or manually create _quarto.yml
```

**Example Structure with Notebooks**:
```
docs/
├── _quarto.yml
├── index.qmd
├── getting-started/
│   ├── installation.qmd
│   └── quickstart.ipynb      # Jupyter notebook!
├── examples/
│   ├── warehouse-queries.ipynb
│   ├── sra-analysis.ipynb
│   └── geo-exploration.ipynb
├── data-warehouse/
│   ├── overview.qmd
│   └── sqlmesh-guide.qmd
└── _freeze/                  # Cached notebook outputs
```

**Example _quarto.yml** (Data Catalog Focus):
```yaml
project:
  type: website
  output-dir: _site

website:
  title: "OmicIDX Data Warehouse"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - href: getting-started/
        text: Getting Started
      - href: data-catalog/
        text: Data Catalog
      - href: schemas/
        text: Schemas
      - href: examples/
        text: Examples
      - href: about/
        text: About
  sidebar:
    - section: "Getting Started"
      contents:
        - getting-started/access.qmd
        - getting-started/remote-database.qmd
        - getting-started/direct-parquet.qmd
    - section: "Data Catalog"
      contents:
        - data-catalog/overview.qmd
        - data-catalog/sra/
        - data-catalog/geo/
        - data-catalog/biosample/
    - section: "Examples"
      contents:
        - examples/common-queries.ipynb
        - examples/joins-across-datasets.ipynb

format:
  html:
    theme: cosmo
    css: styles.css
    code-fold: show
    code-tools: true
    toc: true
    toc-depth: 3

execute:
  freeze: auto  # Only re-run if source changed
  cache: true   # Cache execution results
```

**Including Notebooks in Docs**:
```markdown
<!-- In a .qmd file -->
# Querying the Warehouse

Here's a complete example notebook:

```{python}
#| echo: true
#| output: true
import duckdb
conn = duckdb.connect('warehouse.duckdb')
result = conn.execute("SELECT COUNT(*) FROM bronze.stg_sra_studies").fetchall()
print(f"Total studies: {result[0][0]}")
```

Or include a full notebook:
```{r}
#| label: notebook-example
#| echo: false
knitr::include_graphics("examples/warehouse-queries.ipynb")
```
```

**Python Code Execution**:
```python
# In a .qmd file
```{python}
#| label: query-example
#| echo: true
#| output: true
#| cache: true

import duckdb
from pathlib import Path

# Connect to warehouse
conn = duckdb.connect('../omicidx_warehouse.duckdb')

# Execute query
query = """
SELECT 
    study_type,
    COUNT(*) as count
FROM bronze.stg_sra_studies
GROUP BY study_type
ORDER BY count DESC
LIMIT 10
"""

result = conn.execute(query).df()
print(result.to_markdown())
```
```

**Deployment**:
```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Quarto Docs
on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: quarto-dev/quarto-actions/setup@v2
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - name: Render Quarto
        run: |
          cd docs
          quarto render
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/_site
```

### Option 2: Astro

**Why Astro**:
- **Modern Web Framework**: Component-based, very flexible
- **Notebook Integration**: Via plugins (e.g., `@astrojs/mdx`, `astro-notebook`)
- **Interactive Components**: React/Vue/Svelte components for demos
- **Fast**: Islands architecture, minimal JS
- **Customizable**: Full control over design and functionality

**Notebook Integration**:
- Use `astro-notebook` or `@nteract/notebook-render` components
- Convert notebooks to MDX/Astro components
- Embed interactive widgets
- Custom notebook renderers

**Setup**:
```bash
cd docs
npm create astro@latest . -- --template minimal
npm install @astrojs/mdx @astrojs/react
```

**Example Structure**:
```
docs/
├── astro.config.mjs
├── package.json
├── src/
│   ├── layouts/
│   ├── components/
│   │   └── Notebook.astro
│   └── pages/
│       ├── index.astro
│       ├── examples/
│       │   └── warehouse-queries.mdx
│       └── guides/
└── public/
    └── notebooks/
        └── warehouse-queries.ipynb
```

**Notebook Component Example**:
```astro
---
// src/components/Notebook.astro
import { readFile } from 'fs/promises';
import { parse } from '@nteract/notebook-render';

const notebookPath = Astro.props.path;
const notebookContent = await readFile(notebookPath, 'utf-8');
const notebook = JSON.parse(notebookContent);
---

<div class="notebook">
  {notebook.cells.map(cell => (
    <div class={`cell ${cell.cell_type}`}>
      {cell.cell_type === 'code' && (
        <>
          <pre><code>{cell.source.join('')}</code></pre>
          {cell.outputs && (
            <div class="outputs">
              {cell.outputs.map(output => (
                <pre>{JSON.stringify(output.data)}</pre>
              ))}
            </div>
          )}
        </>
      )}
      {cell.cell_type === 'markdown' && (
        <div set:html={cell.source.join('')} />
      )}
    </div>
  ))}
</div>
```

**Trade-offs**:
- Requires Node.js ecosystem
- More setup complexity
- Better for interactive web apps than pure docs
- Notebook integration requires custom components

### Option 3: MkDocs with Notebook Support

**Why**:
- Python-native
- Can add notebook support via plugins
- Material theme is excellent

**Notebook Integration**:
- `mkdocs-jupyter` plugin: Renders notebooks
- `mkdocs-macros-plugin`: For dynamic content
- Convert notebooks to markdown first

**Trade-offs**:
- Notebook support is less seamless than Quarto
- Requires conversion step or plugin setup
- Less interactive than Quarto

### Comparison Summary

| Feature | Quarto | Astro | MkDocs |
|---------|--------|-------|--------|
| **Notebook Support** | ⭐⭐⭐ Native | ⭐⭐ Via plugins | ⭐ Via plugins |
| **Code Execution** | ⭐⭐⭐ Built-in | ⭐ Manual | ⭐ Via plugins |
| **Python Integration** | ⭐⭐⭐ Excellent | ⭐⭐ Good | ⭐⭐⭐ Native |
| **SQL Support** | ⭐⭐⭐ Excellent | ⭐⭐ Good | ⭐⭐ Good |
| **Learning Curve** | ⭐⭐ Medium | ⭐⭐⭐ Steeper | ⭐ Easy |
| **Customization** | ⭐⭐ Good | ⭐⭐⭐ Excellent | ⭐⭐ Good |
| **Deployment** | ⭐⭐⭐ Easy | ⭐⭐⭐ Easy | ⭐⭐⭐ Easy |
| **Best For** | Data science docs | Interactive web apps | Simple docs |

## Content Strategy: Data Catalog Focus

### Primary Content: Data Discovery and Access

The website should prioritize helping users **find and use the data**, not build the ETL:

1. **Data Catalog Pages** (Primary)
   - What datasets are available?
   - What's in each dataset?
   - How to access (remote DuckDB, direct parquet)
   - Example queries for each dataset

2. **Schema Documentation** (Primary)
   - Detailed table schemas
   - Column descriptions
   - Data types and constraints
   - Relationships between tables

3. **Access Patterns** (Primary)
   - Using the remote DuckDB database
   - Querying parquet files directly
   - Performance considerations
   - Common query patterns

4. **Query Examples** (Primary)
   - Interactive notebooks showing real queries
   - Joins across datasets
   - Aggregations and analysis
   - Visualizations

5. **About/ETL Info** (Secondary)
   - Brief overview of data sources
   - Update frequency
   - Data provenance
   - Link to technical docs for maintainers

### Example Homepage Structure

```markdown
# OmicIDX Data Warehouse

A comprehensive genomics metadata resource available as a frozen data lake.

## Quick Access

- **Remote Database**: Download `omicidx.duckdb` and query directly
- **Direct Parquet**: Query parquet files from R2/S3
- **Data Catalog**: Browse available datasets

## Available Datasets

- **SRA**: ~30M experiments from NCBI Sequence Read Archive
- **GEO**: ~7M samples, ~260K series from Gene Expression Omnibus  
- **BioSample**: ~40M samples from NCBI
- **BioProject**: ~800K projects from NCBI
- **EBI BioSample**: ~10M samples from European Bioinformatics Institute

[Get Started →](getting-started/access.qmd)
[Browse Catalog →](data-catalog/overview.qmd)
```

## Incorporating Notebooks and Code Examples

### Strategy: Focus on Data Usage, Not ETL

Notebooks should demonstrate **how to query and analyze the data**, not how to run ETL:

#### 1. Data Access Examples

**Focus**: How to connect to and query the remote data warehouse

**Example**: `docs/getting-started/first-query.ipynb`
```python
# Connect to remote database
import duckdb

# Download or reference the remote DuckDB file
# (from https://store.yourdomain.com/omicidx.duckdb)
conn = duckdb.connect('omicidx.duckdb')

# Query the data
result = conn.execute("""
    SELECT 
        study_type,
        COUNT(*) as count
    FROM bronze.stg_sra_studies
    GROUP BY study_type
    ORDER BY count DESC
    LIMIT 10
""").df()

print(result)
```

Benefits:
- Shows actual data access patterns
- Interactive - users can run it
- Demonstrates real queries against the warehouse

#### 2. Dataset-Specific Query Examples

Create notebooks for each dataset showing:
- How to query that specific dataset
- Common use cases
- Joins with related tables
- Visualizations and analysis

**Example Structure**:
```
docs/
├── data-catalog/
│   ├── sra/
│   │   ├── index.qmd           # Overview of SRA data
│   │   ├── schema.qmd           # Table schemas
│   │   └── examples.ipynb       # SRA-specific queries
│   │       - Finding studies by organism
│   │       - Joining studies → experiments → runs
│   │       - Platform distributions
│   ├── geo/
│   │   ├── index.qmd
│   │   ├── schema.qmd
│   │   └── examples.ipynb       # GEO-specific queries
│   │       - Series exploration
│   │       - Sample metadata
│   │       - Platform information
│   └── biosample/
│       └── ...
├── examples/
│   ├── cross-dataset-joins.ipynb  # Joining SRA + GEO + BioSample
│   ├── common-patterns.ipynb      # Reusable query patterns
│   └── visualizations.ipynb       # Data exploration plots
```

#### 3. Access Pattern Examples

Show different ways to access the data:

**A. Remote DuckDB Database**:
```python
# docs/getting-started/remote-database.ipynb
import duckdb

# Option 1: Download the database file
# wget https://store.yourdomain.com/omicidx.duckdb
conn = duckdb.connect('omicidx.duckdb')

# Option 2: Query directly from URL (if supported)
# conn = duckdb.connect('https://store.yourdomain.com/omicidx.duckdb')

# The database contains views pointing to parquet files
tables = conn.execute("SHOW TABLES").fetchall()
print("Available tables:", tables)

# Query as normal - DuckDB fetches parquet files automatically
result = conn.execute("SELECT * FROM bronze.stg_sra_studies LIMIT 10").df()
```

**B. Direct Parquet Queries**:
```python
# docs/getting-started/direct-parquet.ipynb
import duckdb

# Query parquet files directly from R2/S3
query = """
SELECT *
FROM read_parquet('https://store.yourdomain.com/data/bronze/stg_sra_studies.parquet')
LIMIT 10
"""

result = duckdb.execute(query).df()
```

**C. Catalog-Based Discovery**:
```python
# docs/examples/using-catalog.ipynb
import json
import requests

# Load the data catalog
catalog_url = "https://store.yourdomain.com/catalog.json"
catalog = requests.get(catalog_url).json()

# Discover available datasets
for dataset in catalog['datasets']:
    print(f"{dataset['name']}: {dataset['description']}")
    print(f"  Tables: {len(dataset['tables'])}")
    print(f"  Location: {dataset['location']}")
```

#### 4. Schema Documentation with Examples

Document each table with:
- Complete schema (columns, types, descriptions)
- Example queries
- Relationships to other tables
- Common use cases

**Quarto Example**:
```markdown
# docs/data-catalog/sra/stg-sra-studies.qmd

# SRA Studies Table

Staging table containing cleaned and standardized SRA study metadata.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| accession | VARCHAR | SRA study accession (e.g., SRP123456) |
| title | VARCHAR | Study title |
| study_type | VARCHAR | Type of study (RNA-Seq, ChIP-Seq, etc.) |
| organism | VARCHAR | Primary organism |
| publish_date | DATE | Publication date |
| ... | ... | ... |

## Example Queries

```{python}
#| echo: true
#| output: true
import duckdb

conn = duckdb.connect('../../omicidx.duckdb')

# Count by study type
query = """
SELECT 
    study_type,
    COUNT(*) as count
FROM bronze.stg_sra_studies
GROUP BY study_type
ORDER BY count DESC
LIMIT 10
"""

result = conn.execute(query).df()
print(result.to_markdown())
```

## Related Tables

- `bronze.stg_sra_experiments` - Experiments in these studies
- `bronze.stg_sra_runs` - Sequencing runs
- `bronze.stg_sra_samples` - Biological samples
```

#### 5. Interactive Dashboards/Visualizations

Use notebooks to create:
- Data quality dashboards
- Schema exploration tools
- Query builders
- Interactive examples

**With Plotly/Altair**:
```python
# In a Quarto notebook
```{python}
#| echo: false
#| output: true
import plotly.express as px
import duckdb

conn = duckdb.connect('warehouse.duckdb')
df = conn.execute("""
    SELECT 
        DATE_TRUNC('month', publish_date) as month,
        COUNT(*) as studies
    FROM bronze.stg_sra_studies
    GROUP BY month
    ORDER BY month
""").df()

fig = px.line(df, x='month', y='studies', 
              title='SRA Studies Over Time')
fig.show()
```
```

### Notebook Organization Best Practices

1. **Keep Notebooks Executable**: Ensure they can run standalone
2. **Use Relative Paths**: Reference warehouse/data relative to repo root
3. **Cache Expensive Operations**: Use Quarto's freeze feature
4. **Version Control**: Commit both `.ipynb` and executed outputs
5. **Clear Structure**: One notebook per topic/example
6. **Documentation**: Add markdown cells explaining each step

### Example: Data Access Notebook

**Focus on using the data, not building it**:

```python
# docs/getting-started/first-query.ipynb
# Cell 1: Markdown
"""
# Your First Query

This notebook shows how to access and query the OmicIDX data warehouse.

The warehouse is available as:
1. **Remote DuckDB database** - Pre-configured views pointing to parquet files
2. **Direct parquet files** - Query files directly from R2/S3

## Getting the Database

Download the remote database:
```bash
wget https://store.yourdomain.com/omicidx.duckdb
```

Or use it directly (if your DuckDB version supports it).
"""

# Cell 2: Code
import duckdb

# Connect to the remote database
# (Assumes you've downloaded omicidx.duckdb)
conn = duckdb.connect('omicidx.duckdb')

# Cell 3: Code (with output)
# List available schemas and tables
schemas = conn.execute("SHOW SCHEMAS").df()
print("Available schemas:")
print(schemas)

tables = conn.execute("SHOW TABLES").df()
print(f"\nTotal tables: {len(tables)}")

# Cell 4: Markdown
"""
## Your First Query

Let's query the SRA studies table:
"""

# Cell 5: Code (SQL with results)
result = conn.execute("""
    SELECT 
        study_type,
        COUNT(*) as count
    FROM bronze.stg_sra_studies
    GROUP BY study_type
    ORDER BY count DESC
    LIMIT 10
""").df()

print(result.to_markdown())

# Cell 6: Markdown
"""
## Next Steps

- Browse the [Data Catalog](data-catalog/overview.qmd) to see all available datasets
- Check out [example queries](examples/common-queries.ipynb)
- Read about [access patterns](getting-started/access.qmd)
"""
```

### Integration with Data Catalog

**Link to Catalog JSON**:
```markdown
<!-- In docs -->
The complete data catalog is available at:
[Catalog JSON](https://store.yourdomain.com/catalog.json)

This catalog contains metadata about all tables, columns, and file locations.
```

**Reference Actual Data**:
```markdown
<!-- Show real data examples -->
```{python}
#| echo: true
#| output: true
import duckdb

# Query actual deployed data
conn = duckdb.connect('https://store.yourdomain.com/omicidx.duckdb')
result = conn.execute("SELECT COUNT(*) FROM bronze.stg_sra_studies").fetchone()
print(f"Total SRA studies: {result[0]:,}")
```
```

**Schema Auto-Documentation**:
- Generate schema docs from `catalog.json`
- Auto-update when warehouse is redeployed
- Show column types, descriptions, sample data

## Content Organization Strategy

### 1. Primary Content: Data Catalog

**Focus**: Help users discover and use the data

- **Homepage**: What data is available, quick access links
- **Data Catalog**: Browse datasets (SRA, GEO, BioSample, etc.)
  - Overview of each dataset
  - Schema documentation
  - Example queries
  - Access patterns
- **Getting Started**: How to access the data
  - Remote DuckDB usage
  - Direct parquet queries
  - First query examples
- **Schemas**: Detailed table documentation
- **Examples**: Interactive query notebooks

### 2. Secondary Content: About/ETL Info

**Focus**: Transparency about how the warehouse is built (for interested users)

- **About/Data Sources**: Brief overview of source data
- **About/Update Frequency**: How often data is refreshed
- **About/Architecture**: High-level warehouse structure
- **Link to Technical Docs**: Point to `sqlmesh/README.md` for maintainers

### 3. Keep Technical Docs in Place

- `sqlmesh/README.md` → Keep as-is, link from "About" section
- `DEPLOYMENT.md` → Keep as-is (for maintainers)
- Component READMEs → Keep in place
- ETL code → Document minimally, focus is on the data product

### 3. Link to Data, Not Code

Use links to the actual data product:
```markdown
- [Download Database](https://store.yourdomain.com/omicidx.duckdb)
- [View Catalog](https://store.yourdomain.com/catalog.json)
- [Query Examples](examples/common-queries.ipynb)

For technical details about how the warehouse is built, see the
[SQLMesh documentation](../sqlmesh/README.md) (for maintainers).
```

## Deployment Options

### GitHub Pages (Simplest)

```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Documentation
on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - '.github/workflows/deploy-docs.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --group docs
      - run: cd docs && uv run mkdocs gh-deploy --force
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Cloudflare Pages / Netlify / Vercel

All support static site deployment with similar workflows.

## Integration with Data Warehouse

### Strategy: Document the Data Product

1. **Primary focus**: The deployed data warehouse (parquet files, remote DB)
2. **Link to actual data**: Reference the deployed catalog and database
3. **Keep ETL docs separate**: Technical docs stay in repo, linked from "About"
4. **Auto-generate where possible**: Schema docs from catalog.json

Example homepage:
```markdown
<!-- docs/index.qmd -->
# OmicIDX Data Warehouse

A comprehensive genomics metadata resource.

## Quick Access

- **Remote Database**: [Download omicidx.duckdb](https://store.yourdomain.com/omicidx.duckdb)
- **Data Catalog**: [View catalog.json](https://store.yourdomain.com/catalog.json)
- **Documentation**: Browse datasets and schemas below

## Available Datasets

[Browse the data catalog →](data-catalog/overview.qmd)

## Getting Started

[Learn how to access and query the data →](getting-started/access.qmd)

## About

[Learn about data sources and update frequency →](about/data-sources.qmd)
[Technical documentation for maintainers →](../sqlmesh/README.md)
```

## Final Recommendation

### For Your Use Case: **Quarto** ⭐

Given your requirements:
- ✅ Need notebook support (Jupyter `.ipynb` files)
- ✅ Python code examples
- ✅ SQL query demonstrations
- ✅ Data science/ETL documentation
- ✅ Interactive examples

**Quarto is the clear winner** because:
1. **Native notebook support** - No conversion needed
2. **Code execution** - Can run Python/SQL during build
3. **Perfect for data science** - Built for this use case
4. **Beautiful output** - Professional documentation sites
5. **Easy deployment** - Works with GitHub Pages, Netlify, etc.

### Alternative: Astro (if you need more customization)

Choose Astro if:
- You want a more web-app-like experience
- You need custom React/Vue components
- You want maximum design flexibility
- Notebook support via plugins is acceptable

### Quick Start with Quarto

```bash
# 1. Install Quarto (one-time)
# https://quarto.org/docs/get-started/

# 2. Initialize docs directory
cd /home/davsean/Documents/git/omicidx-gh-etl
quarto create-project docs --type website

# 3. Create first notebook example
cd docs
jupyter notebook examples/warehouse-quickstart.ipynb

# 4. Render and preview
quarto preview

# 5. Build for production
quarto render
```

## Next Steps

1. **Choose SSG**: **Quarto** (recommended) or Astro
2. **Create `docs/` structure**: Initialize Quarto project
3. **Convert first example**: Transform `warehouse_quickstart.py` → notebook
4. **Set up deployment**: GitHub Pages with Quarto Actions
5. **Iterate**: Add notebooks and content incrementally

## Alternative: Keep Docs in Root

If you prefer not to have a `docs/` subdirectory, you could:

```
omicidx-gh-etl/
├── website/              # Website source
│   ├── mkdocs.yml
│   └── docs/
└── ... (rest of repo)
```

But `docs/` is more conventional and clearer.

