# Compiling picorv

```bash
NX_SEED=0 PYTHONPATH=$PYTHONPATH:$(pwd)/work:$(readlink -f ../common/python) python3 py_nxcompile ../tests/picorv32/work/picorv32_nl.v
```

# Compiling basic example

```bash
NX_SEED=0 PYTHONPATH=$PYTHONPATH:$(pwd)/work:$(readlink -f ../common/python) python3 py_nxcompile ../tests/multilayer/work/Top_nl.v
```

# Compiling handwritten example

```bash
NX_SEED=0 PYTHONPATH=$PYTHONPATH:$(pwd)/work:$(readlink -f ../common/python) python3 py_nxcompile ./tests/adder_4.v
```

# Running a compiled design

```bash
../nxmodel/work/nxmodel --rows 1 --columns 1 --cycles 10 --vcd run.vcd --verbose summary.json
```

# Running tests with coverage

```bash
PYTHONPATH=$PYTHONPATH:$(pwd)/../common/python:$(pwd)/work python3 -m pytest --cov=py_nxcompile --cov-report html:cov_html tests/python
```
