"""Offline contestant dependency smoke check; no challenge or answer access."""
import importlib
import shutil
import subprocess
import sys


def main():
    failures = []
    for module in ('Crypto', 'requests', 'sympy', 'PIL', 'mmh3', 'numpy',
                   'scipy.optimize', 'z3', 'pwn', 'uncompyle6'):
        try:
            importlib.import_module(module)
        except Exception as exc:
            failures.append(f'{module}: {type(exc).__name__}: {exc}')
    for tool in ('gcc', 'g++', 'make', 'objdump', 'file', 'curl', 'nc',
                 'openssl', 'unzip', '7z', 'gdb', 'socat', 'tcpdump',
                 'xxd', 'exiftool', 'php'):
        if shutil.which(tool) is None:
            failures.append(f'{tool}: executable missing')
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1

    import mmh3
    import numpy as np
    from scipy.optimize import milp, Bounds
    import z3
    from pwn import p32, u32
    assert mmh3.hash('foo') == -156908512
    result = milp(c=np.array([1.0]), integrality=np.ones(1), bounds=Bounds([2], [3]))
    assert result.success and abs(result.x[0] - 2) < 1e-8
    x = z3.Int('x')
    solver = z3.Solver()
    solver.add(x == 7)
    assert solver.check() == z3.sat and solver.model()[x].as_long() == 7
    assert u32(p32(12345)) == 12345
    for command in (['php', '-r', 'exit(extension_loaded("json") ? 0 : 1);'],
                    ['exiftool', '-ver'], ['xxd', '-v']):
        subprocess.run(command, check=True, capture_output=True)
    print('CTF dependency check passed (imports, executables, hash, MILP, SMT, binary packing, PHP JSON).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
