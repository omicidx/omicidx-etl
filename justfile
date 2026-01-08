# Enable dotenv loading to manage environment variables 
set dotenv-load := true

# sqlmesh commands

# Run sqlmesh plan
[group('sqlmesh')]
plan:
    cd sqlmesh && uv run sqlmesh plan

# Run sqlmesh plan for specific environment
[group('sqlmesh')]
plan-env ENV:
    cd sqlmesh && uv run sqlmesh plan {{ENV}}

# Run sqlmesh tests
[group('sqlmesh')]
test:
    cd sqlmesh && uv run sqlmesh test

# Audit sqlmesh models
[group('sqlmesh')]
audit:
    cd sqlmesh && uv run sqlmesh audit

# Clean sqlmesh cache
[group('sqlmesh')]
clean:
    cd sqlmesh && uv run sqlmesh clean




# Run `oidx sra extract`
[group('oidx')]
sra-extract:
	uv run oidx sra sync --dest ${OMICIDX_DATA_ROOT}

# Run `oidx geo extract`
[group('oidx')]
geo-extract:
	uv run oidx geo extract # ${OMICIDX_DATA_ROOT}

# Run `oidx biosample extract`
[group('oidx')]
biosample-extract:
	uv run oidx biosample extract ${OMICIDX_DATA_ROOT}

# Run `oidx ebi_biosample extract`
[group('oidx')]
ebi-biosample-extract:
	uv run oidx ebi-biosample extract ${OMICIDX_DATA_ROOT}

# Run `oidx europepmc extract`
[group('oidx')]
europepmc-extract:
	uv run oidx europepmc extract ${OMICIDX_DATA_ROOT}

# Run `oidx icite extract`
[group('oidx')]
icite-extract:
    uv run oidx icite extract ${OMICIDX_DATA_ROOT}

# Run `oidx pubmed extract`
[group('oidx')]
pubmed-extract:
    uv run oidx pubmed extract ${OMICIDX_DATA_ROOT}



# oidx commands
[group('oidx')]
extract-all: geo-extract biosample-extract europepmc-extract pubmed-extract
