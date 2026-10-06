"""Static self-check for a workshop axis team's hand-off chain (dev tool, not packed into the zip).

Compares the chain you designed (EXPECTED) with every literal
    self._force_switch_to(self._find_teammate('X'), 'mode')
written inside each class's perform_* methods. Run it before every repack.

Axis model: f modes = startup axis (once per fight), s modes = loop axis (repeats, closed).
Exactly one f->s edge (STARTUP_END) joins them; every edge leaving an s mode must go to an s mode and close the loop.

Usage: python verify_chain.py [team_dir]    (default: this script's directory)
Exit code: 0 = PASS, 1 = FAIL.

Replace FILES / EXPECTED / STARTUP_END / PENDING below with your team's chain.
After adding a new assertion, break one edge on purpose and confirm the exit code is 1.
"""
import ast
import pathlib
import sys

# Class names; each must live in <ClassName>.py inside team_dir.
FILES = ('Alpha', 'Beta', 'Gamma')

# (source class, source mode, target class, target mode)
# Startup axis: Alpha f1 -> Beta f1 -> Gamma f1 -> Alpha f2 -> Gamma f2 -> Beta s1
# Loop axis:    Beta s1 -> Gamma s1 -> Alpha s1 -> Beta s1 (closed)
EXPECTED = [
    ('Alpha', 'f1', 'Beta', 'f1'),
    ('Beta', 'f1', 'Gamma', 'f1'),
    ('Gamma', 'f1', 'Alpha', 'f2'),
    ('Alpha', 'f2', 'Gamma', 'f2'),
    ('Gamma', 'f2', 'Beta', 's1'),
    ('Beta', 's1', 'Gamma', 's1'),
    ('Gamma', 's1', 'Alpha', 's1'),
    ('Alpha', 's1', 'Beta', 's1'),
]

# Endpoints whose perform_<mode> is not written yet: {('Class', 'mode'), ...}
PENDING = set()
# The single f->s edge that ends the startup axis.
STARTUP_END = ('Gamma', 'f2', 'Beta', 's1')

WIDTH = max(len(name) for name in FILES)


def _target_of(call):
    """Extract ('X', 'mode') from _force_switch_to(self._find_teammate('X'), 'mode')."""
    target = mode = None
    if call.args and isinstance(call.args[0], ast.Call) and call.args[0].args:
        arg0 = call.args[0].args[0]
        if isinstance(arg0, ast.Constant):
            target = arg0.value
    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
        mode = call.args[1].value
    return target, mode


def scan(root):
    edges, methods = [], {}
    for name in FILES:
        tree = ast.parse((root / f'{name}.py').read_text(encoding='utf-8'))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for fn in (f for f in cls.body if isinstance(f, ast.FunctionDef)):
                methods.setdefault(name, set()).add(fn.name)
                if not fn.name.startswith('perform_'):
                    continue
                for call in ast.walk(fn):
                    if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                            and call.func.attr == '_force_switch_to'):
                        target, mode = _target_of(call)
                        edges.append((name, fn.name[len('perform_'):], target, mode))
    return edges, methods


def _fmt(e):
    return f'{e[0]:{WIDTH}} {e[1]}  ->  {e[2]}.{e[3]}'


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
    edges, methods = scan(root)
    ok = True

    print('=== Hand-offs found in code ===')
    for e in edges:
        print(f'  {_fmt(e)}')

    print('=== Compared with EXPECTED ===')
    for exp in EXPECTED:
        hit = exp in edges
        ok &= hit
        print(f'  {"OK     " if hit else "MISSING"} {_fmt(exp)}')
    extra = [e for e in edges if e not in EXPECTED]
    for e in extra:
        print(f'  UNEXPECTED {_fmt(e)}')
    ok &= not extra

    print('=== Axis boundary: exactly one f->s edge, s modes form a closed loop ===')
    f2s = [e for e in edges if not e[1].startswith('s') and e[3] and e[3].startswith('s')]
    s2s = [e for e in edges if e[1].startswith('s')]
    loop = [e for e in EXPECTED if e[1].startswith('s')]
    if f2s == [STARTUP_END]:
        print(f'  OK  single f->s edge {_fmt(STARTUP_END)} (startup end)')
    else:
        ok = False
        for e in f2s:
            print(f'  BAD f->s edge {_fmt(e)} (expected only {_fmt(STARTUP_END)}); startup axis cut short?')
        if not f2s:
            print('  BAD no f->s edge: the startup axis never reaches the loop axis')
    if sorted(s2s) == sorted(loop):
        print(f'  OK  {len(s2s)} edges leaving s modes match EXPECTED')
    else:
        ok = False
        for e in sorted(set(s2s) - set(loop), key=str):
            print(f'  BAD extra edge leaving an s mode {_fmt(e)}')
        for e in sorted(set(loop) - set(s2s), key=str):
            print(f'  BAD missing edge leaving an s mode {_fmt(e)}')
    # Closure: every mode entered by an s edge must also leave by an s edge, or the loop breaks there.
    srcs = {(e[0], e[1]) for e in loop}
    dsts = {(e[2], e[3]) for e in loop}
    if srcs == dsts:
        print(f'  OK  closed loop: {len(srcs)} s modes, each entered and left once')
    else:
        ok = False
        for n in sorted(dsts - srcs, key=str):
            print(f'  BAD {n[0]}.{n[1]} has an s in-edge but no s out-edge: the loop breaks here')
        for n in sorted(srcs - dsts, key=str):
            print(f'  BAD {n[0]}.{n[1]} has an s out-edge but no s in-edge: unreachable')

    print('=== Target perform_<mode> exists ===')
    for src, src_mode, target, mode in edges:
        hit = target in methods and f'perform_{mode}' in methods[target]
        pending = (target, mode) in PENDING
        ok &= hit or pending
        if hit:
            print(f'  OK      {target}.perform_{mode}')
        elif pending:
            print(f'  PENDING {target}.perform_{mode}')
        elif target is None or mode is None:
            print(f'  BAD     {src}.perform_{src_mode}: _force_switch_to is not the literal form')
        else:
            print(f'  BAD     {target}.perform_{mode} does not exist')

    print('\nHand-off chain check:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
