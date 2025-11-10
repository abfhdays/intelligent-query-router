# Intelligent Query Router

Automatically selects optimal SQL execution backend (DuckDB/Polars/Spark) based on query characteristics.

## Features (Planned)

- ✅ SQLGlot-based SQL parsing and optimization
- 🚧 Partition pruning (50-100x speedups)
- 🚧 Intelligent backend selection
- 🚧 Query result caching
- 🚧 CLI interface

## Installation
```bash
# Clone repository
git clone <your-repo>
cd intelligent-query-router

# Setup environment
python -m venv venv
source venv/bin/activate

# Install
pip install -e .
```
## Setup (For devs)
1. Think/research about partition pruning (what data types are input and output, intermediate states, what data structures are need for sqlglot modules, (parser, optimizer etc.))
2. Same for query caching

- Create basic type definitions for backend sanititation
- Create test suite for each module and integration testing
- Cli dev


## Usage
```bash
# Execute query
irouter execute "SELECT * FROM sales WHERE date >= '2024-11-01'"

# Explain query plan
irouter explain "SELECT * FROM sales WHERE date >= '2024-11-01'"
```

## Development Status

Day 1: Project setup ✅
Day 2: Partition pruning 🚧
Day 3: Backend selection 📅
Day 4: Query caching 📅
Day 5: CLI polish 📅
Day 6: Testing 📅
Day 7: Documentation 📅x