# CTF contestant environment

Build from the repository root:

```powershell
docker build -t agent-olympiad-ctf:v1 docker/ctf
```

The image preinstalls Python crypto, numerical optimisation, SMT, binary-analysis
and bytecode-analysis dependencies in `requirements.txt`, plus the command-line
tools checked by `check_dependencies.py`. These cover the missing imports and
executables observed in the 2026-09-17 Cybench mini traces. Upstream challenge
services retain their own Dockerfiles and dependencies.

The build runs `pip check` and a dependency smoke check. To verify the image under
the contestant's runtime restrictions, without models or challenge access:

```powershell
docker run --rm --network none --memory 1g --cpus 1 --pids-limit 256 --cap-drop ALL --security-opt no-new-privileges:true agent-olympiad-ctf:v1 python /opt/ctf/check_dependencies.py
```

Contestant networks intentionally have no external package-index access. Add
required packages at image build time; do not rely on runtime downloads.
Installing a decompiler does not imply it supports every Python bytecode version.
Use its supported bytecode formats or the included `xdis` tooling where appropriate.

New containers use the rebuilt image. Existing containers retain their original
image and workspace; do not force-recreate an in-progress experiment to upgrade
dependencies. Use a fresh run/output identity for experiments after this change.
Historical scores remain unchanged.
