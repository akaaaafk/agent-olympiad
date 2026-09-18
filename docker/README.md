# Local execution environments

Build from the repository root (Docker Desktop must be running):

```powershell
docker pull python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
docker pull gcc:14
docker build -t agent-olympiad-python-tools:v1 docker/python-tools
docker build -t agent-olympiad-latex:v1 docker/latex
docker build -t agent-olympiad-ctf:v1 docker/ctf
```

| Execution path | Environment | Contract |
| --- | --- | --- |
| General `execute_code` computation | `agent-olympiad-python-tools:v1` | NumPy, SciPy, SymPy, pandas, Matplotlib; one BLAS thread; headless plotting with writable temporary cache |
| Python programming judge | Pinned Python 3.11 slim | Existing standard-library environment and sandbox limits |
| C++17 programming judge | Package image, default `gcc:14` | Compile with g++ and deliver test stdin through Docker `-i` |
| MCM/ICM LaTeX | `agent-olympiad-latex:v1` | Base/recommended/extra/science/pictures packages; pdflatex; shell escape disabled |
| Cybench and NYU CTF | `agent-olympiad-ctf:v1` plus upstream services | See `ctf/README.md`; contestant tools do not change challenge-server dependencies |

Run the model-free integration check:

```powershell
& ..\.venv\Scripts\python.exe scripts/smoke_docker_dependencies.py
```

This verifies Python stdin, scientific calculation and plotting through the real
code tool, C++ compilation and stdin-based judging, actual LaTeX PDF compilation,
and dependency availability through fresh NYU static and Cybench service task
containers. It uses the production isolation settings and removes only the
temporary containers it creates. It does not submit to remote judges or invoke
models. `--only python|science|cpp|latex|ctf` selects one check.

The 2026-09-17 audit reproduced missing NumPy in the general code tool, missing
LaTeX siunitx, and a C++ stdin delivery failure (a correct doubling program was
judged WA without Docker `-i`). All three were repaired and verified through the
actual execution paths. The CTF dependency repair also applies to NYU CTF.

These checks cover shared execution environments and representative CTF routes,
not every publisher challenge, every possible third-party library, or remote
VJudge availability. They do not promote dataset readiness or change scoring.
Existing containers keep their original image. Use fresh experiment outputs
after runtime changes; do not overwrite historical results. The previous CTF and
LaTeX images are retained as `:before-deps-20260917` on the audited machine.
