# OmicIDX Documentation Site

This directory contains the Quarto-based documentation site for the OmicIDX Data Warehouse.

## Setup

1. **Install Quarto**: https://quarto.org/docs/get-started/

2. **Preview the site**:
   ```bash
   cd docs
   quarto preview
   ```

3. **Render the site**:
   ```bash
   quarto render
   ```

## Structure

- `index.qmd` - Homepage
- `getting-started/` - Access guides
- `data-catalog/` - Dataset documentation
- `schemas/` - Table schemas (to be populated)
- `examples/` - Interactive query notebooks
- `about/` - Background information

## Customization

- `_quarto.yml` - Site configuration
- `custom.scss` - Material Design theme overrides
- `styles.css` - Additional custom styles

## Deployment

The site can be deployed to:
- GitHub Pages
- Netlify
- Cloudflare Pages
- Any static hosting

See `.github/workflows/deploy-docs.yml` for GitHub Pages deployment.

