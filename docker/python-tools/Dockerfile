FROM python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
COPY requirements.txt /opt/python-tools/requirements.txt
RUN pip install --no-cache-dir -r /opt/python-tools/requirements.txt && pip check
# The production sandbox has a 32-process/thread limit and a read-only root.
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp/matplotlib
RUN python -c "import numpy, scipy.optimize, sympy, pandas, matplotlib.pyplot"
WORKDIR /tmp
