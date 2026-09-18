"""Real, model-free checks of local Docker execution paths."""
import argparse
from pathlib import Path
import sys
import tempfile
import hashlib
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

SCIENCE_SOURCE = '''import numpy as np
import pandas as pd
import sympy as sp
from scipy.optimize import linprog
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
assert np.linalg.solve([[2.0]], [6.0])[0] == 3
assert pd.Series([1,2,3]).sum() == 6
x = sp.Symbol('x')
assert sp.solve(x-3,x) == [3]
assert linprog([1],bounds=[(2,3)],method='highs').success
plt.plot([0,1],[0,1]); plt.savefig('/tmp/probe.png')
print('SCIENCE_OK')
'''
LATEX_SOURCE = r'''\documentclass{article}
\usepackage{amsmath,amssymb,booktabs,geometry,hyperref}
\usepackage{siunitx,multirow,enumitem,algorithm,algpseudocode,tikz,pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\section{Environment probe}
\begin{itemize}[nosep]\item Test \num{1234.5}\end{itemize}
\begin{tabular}{ll}\toprule A & B\\\midrule 1 & 2\\\bottomrule\end{tabular}
\begin{algorithm}\begin{algorithmic}\State $x\gets 1$\end{algorithmic}\end{algorithm}
\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}
\end{document}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--science-image')
    parser.add_argument('--latex-image')
    parser.add_argument('--only', choices=['python','science','cpp','latex','ctf'])
    args = parser.parse_args()
    from isolated_python import run_python_isolated, PYTHON_TOOLS_IMAGE
    from artifacts.latex import compile_latex
    from judge.models import ProblemPackage, Limits, TestCase
    from judge.runners import DockerProgrammingJudge
    failures = []
    with tempfile.TemporaryDirectory(prefix='ao_dependency_smoke_') as folder:
        root = Path(folder)
        for name in ('python','science','cpp','latex','ctf'):
            if args.only and args.only != name:
                continue
            try:
                if name == 'python':
                    result = run_python_isolated('print(int(input()) * 2)', stdin='21\n')
                    assert result.returncode == 0 and result.stdout == '42\n', result
                elif name == 'science':
                    options = {'image': args.science_image or PYTHON_TOOLS_IMAGE}
                    result = run_python_isolated(SCIENCE_SOURCE, timeout_sec=15, **options)
                    assert result.returncode == 0 and 'SCIENCE_OK' in result.stdout, result
                    if not args.science_image:
                        from env import OlympiadEnvironment
                        receipt = OlympiadEnvironment._run_code(None, SCIENCE_SOURCE)
                        assert receipt.startswith('Code output:') and 'SCIENCE_OK' in receipt, receipt
                elif name == 'cpp':
                    inp, ans = root/'input.txt', root/'answer.txt'
                    inp.write_text('21\n'); ans.write_text('42\n')
                    package = ProblemPackage('smoke', root, Limits(2000,256,1024), {'type':'token'}, (), ())
                    results, error = DockerProgrammingJudge(package).run(
                        '#include <bits/stdc++.h>\nint main(){int x;std::cin>>x;std::cout<<x*2<<"\\n";}',
                        (TestCase('double',inp,ans),))
                    assert not error and results[0].verdict == 'AC', (error,results)
                elif name == 'latex':
                    compile_latex(LATEX_SOURCE, root/'probe.pdf', image_id=args.latex_image)
                    assert (root/'probe.pdf').stat().st_size > 1000
                else:
                    from ctf_environment_runtime import execute, controller
                    for cid, tid in [('nyu_ctf_bench','nyu_ctf_2013f-cry-stfu'),
                                     ('cybench','cybench_project-sekai-ctf_sekaictf-2022_crypto_diffecient')]:
                        run_id = 'dependency-smoke-' + uuid.uuid4().hex
                        stage, project = controller.directory(tid, 'session-' + hashlib.sha256(run_id.encode()).hexdigest()[:24])
                        try:
                            assert execute(cid,tid,run_id,'start_environment',{})['valid']
                            result = execute(cid,tid,run_id,'execute_environment_command',
                                             {'command':'python /opt/ctf/check_dependencies.py'})
                            assert not result.get('command_failed') and 'check passed' in result['result'], result
                            print(cid + ': dependency check through real runtime PASS', flush=True)
                        finally:
                            if (stage/'compose.yaml').exists():
                                controller.compose(stage,project,'down','--remove-orphans')
                print(name + ': PASS', flush=True)
            except Exception as exc:
                failures.append(name)
                print(name + ': FAIL ' + str(exc)[-2500:], flush=True)
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
