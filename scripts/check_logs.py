"""按 references/logging.md 的词表和规则检查角色代码里的日志调用。

用法（用 ok-ww 自带的 Python，带 -I -B）：
    python.exe -I -B check_logs.py <角色 .py> [<角色 .py> ...]

- 词表从本仓库 references/logging.md 的事件、字段、耗时字段、reason 四张表读取，改表即改检查。
- 检查的调用：self._trace(...)、self.logger.<级别>(...)、self._raw_logger.<级别>(...)、
  getattr(self, '_raw_logger', self.logger).<级别>(...)。_trace 和 _InfoAsDebug 内部的写出行不查。
- `wait` 行只查 `self.task.wait_until` 且上限能从字面量或类常量读出的调用；手写轮询循环要人工看。
- 每条问题输出一行 `<文件>:<行> <规则> <说明>`；probe 行只列出、不算问题。
- 没有问题时退出码 0，有问题时退出码 1。
"""

import argparse
import ast
import os
import re
import sys

LOGGING_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references', 'logging.md')
LEVELS = {'debug', 'info', 'warning', 'error', 'exception', 'critical'}
LOGGER_RECEIVERS = {'self.logger', 'self._raw_logger', "getattr(self, '_raw_logger', self.logger)"}
# 日志实参里允许的调用：只做格式转换，不读游戏状态
SAFE_CALLS = {'str', 'int', 'float', 'bool', 'round', 'abs', 'min', 'max', 'len', 'time.time'}
SAFE_METHODS = {'upper', 'lower'}
SKIP_FUNCS = {'_trace'}
SKIP_CLASSES = {'_InfoAsDebug'}
ATTEMPT_EVENTS = ('cast ', 'retry ', 'switch')
LONG_WAIT = 2.0
TABLES = {'### 事件词表': 'events', '**字段**': 'fields', '**耗时字段**': 'fields', '## L-7 reason 词表': 'reasons'}


def load_vocab(path):
    """Read the first-column `code` cells of the vocab tables; a cell with <...> is a prefix."""
    vocab = {'events': set(), 'prefixes': set(), 'fields': set(), 'reasons': set()}
    table = None
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line in TABLES:
                table = TABLES[line]
                continue
            if line.startswith('#'):
                table = None
            if table is None or not line.startswith('| `'):
                continue
            for token in re.findall(r'`([^`]+)`', line.split('|')[1]):
                if table == 'events' and '<' in token:
                    vocab['prefixes'].add(token.split('<')[0])
                else:
                    vocab[table].add(token)
    return vocab


def text_of(node):
    """Literal text of a str / f-string node; formatted parts become {}."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return ''.join(v.value if isinstance(v, ast.Constant) else '{}' for v in node.values)
    return None


def str_constants(node):
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def state_calls(nodes):
    """Calls in the log arguments other than plain conversions (L-8)."""
    found = []
    for node in nodes:
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            name = ast.unparse(sub.func)
            if name in SAFE_CALLS:
                continue
            if isinstance(sub.func, ast.Attribute) and sub.func.attr in SAFE_METHODS:
                continue
            found.append(name)
    return found


def parse_message(text):
    """Split a logger message into (event, fields, reason) per the L-2 template."""
    body = re.sub(r'^\[[^\]]*\] ', '', text)
    event = re.split(r': (?=ok\b|fail\b)| (?=[a-z_][a-z0-9_]*=)', body)[0]
    fields = re.findall(r'(?:^|\s)([a-z_][a-z0-9_]*)=', body)
    reason = re.search(r'reason=([a-z_]+)', body)
    return event, [f for f in fields if f != 'reason'], [reason.group(1)] if reason else []


def class_constants(tree):
    """Numeric class attributes (NAME = 2.5) of every class in the file."""
    constants = {}
    for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        for stmt in cls.body:
            if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, (int, float))):
                constants[stmt.targets[0].id] = stmt.value.value
    return constants


def log_event(stmt):
    """Event text of a statement that is a single _trace / logger call, else None."""
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)):
        return None
    call = stmt.value
    if call.func.attr == '_trace' and len(call.args) > 1:
        return text_of(call.args[1])
    if call.func.attr in LEVELS and call.args:
        text = text_of(call.args[0])
        return parse_message(text)[0] if text is not None else None
    return None


class Checker(ast.NodeVisitor):
    def __init__(self, path, vocab, tree):
        self.path = path
        self.vocab = vocab
        self.constants = class_constants(tree)
        self.parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        self.problems = []
        self.probes = []
        self.scope = []

    def report(self, node, rule, message):
        self.problems.append(f'{self.path}:{node.lineno} {rule} {message}')

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node):
        self.generic_visit(node)
        if any(name in SKIP_FUNCS or name in SKIP_CLASSES for name in self.scope):
            return
        func = node.func
        if not isinstance(func, ast.Attribute):
            return
        if func.attr == 'wait_until' and ast.unparse(func.value) == 'self.task':
            self.check_wait(node)
        elif func.attr == '_trace' and ast.unparse(func.value) == 'self':
            self.check_trace(node)
        elif func.attr in LEVELS and ast.unparse(func.value) in LOGGER_RECEIVERS:
            self.check_logger(node, func.attr)

    def check_wait(self, node):
        """L-3: a wait_until with a timeout of LONG_WAIT or more is preceded by a `wait:` line."""
        value = next((k.value for k in node.keywords if k.arg == 'time_out'), node.args[1] if len(node.args) > 1 else None)
        if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
            time_out = value.value
        elif isinstance(value, ast.Attribute) and ast.unparse(value.value) == 'self':
            time_out = self.constants.get(value.attr)
        else:
            time_out = None
        if time_out is None or time_out < LONG_WAIT:
            return
        stmt = node
        while not isinstance(stmt, ast.stmt):
            stmt = self.parents[stmt]
        siblings = next((body for body in (getattr(self.parents[stmt], f, None) for f in ('body', 'orelse', 'finalbody'))
                         if isinstance(body, list) and stmt in body), [])
        index = siblings.index(stmt) if stmt in siblings else 0
        event = log_event(siblings[index - 1]) if index > 0 else None
        if not (event or '').startswith('wait:'):
            self.report(node, 'L-3', f'上限 {time_out}s 的 wait_until 前没有 wait 行')

    def known_event(self, event):
        return event in self.vocab['events'] or any(event.startswith(p) for p in self.vocab['prefixes'])

    def check_common(self, node, level, event, fields, reasons, values):
        if event is None:
            return
        probe = event.startswith('probe ')
        if probe:
            self.probes.append(f'{self.path}:{node.lineno} probe {event[6:]}')
        if level != 'debug' and not probe:
            if not self.known_event(event):
                self.report(node, 'L-2', f'事件不在词表：{event}')
            for field in fields:
                if field not in self.vocab['fields']:
                    self.report(node, 'L-6', f'字段不在词表：{field}')
        for reason in reasons:
            if reason not in self.vocab['reasons']:
                self.report(node, 'L-7', f'reason 不在词表：{reason}')
        for field, value in values.items():
            if field.endswith('_s') and re.fullmatch(r'self\.[A-Z][A-Z0-9_]*', ast.unparse(value)):
                self.report(node, 'L-5', f'{field} 写的是常量 {ast.unparse(value)}，不是实测耗时')
        if level in ('error', 'exception', 'critical'):
            self.report(node, 'L-1', '角色代码不用 error 级别')
        is_fallback = event.startswith('fallback')
        if is_fallback and level != 'warning':
            self.report(node, 'L-1', 'fallback 必须打 warning')
        if level == 'warning' and not is_fallback:
            self.report(node, 'L-1', 'warning 只用于 fallback')

    def check_trace(self, node):
        event = text_of(node.args[1]) if len(node.args) > 1 else None
        keywords = {k.arg: k.value for k in node.keywords if k.arg}
        if event is not None and event.startswith(ATTEMPT_EVENTS) and 'ok' not in keywords:
            self.report(node, 'L-2', f'{event} 没带 ok；没有确认信号的发键写 send')
        fields = [k for k in keywords if k not in ('ok', 'reason')]
        reasons = str_constants(keywords['reason']) if 'reason' in keywords else []
        values = {k: v for k, v in keywords.items() if k not in ('ok', 'reason')}
        self.check_common(node, 'info', event, fields, reasons, values)
        for name in state_calls(list(node.args) + list(keywords.values())):
            self.report(node, 'L-8', f'日志实参里调用了 {name}()，判断时先存进变量')

    def check_logger(self, node, level):
        text = text_of(node.args[0]) if node.args else None
        if text is not None:
            event, fields, reasons = parse_message(text)
            self.check_common(node, level, event, fields, reasons, {})
        for name in state_calls(node.args):
            self.report(node, 'L-8', f'日志实参里调用了 {name}()，判断时先存进变量')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    vocab = load_vocab(LOGGING_MD)
    problems, probes = [], []
    for path in args.files:
        with open(path, encoding='utf-8-sig') as f:
            tree = ast.parse(f.read(), filename=path)
        checker = Checker(path, vocab, tree)
        checker.visit(tree)
        problems += checker.problems
        probes += checker.probes
    for line in problems:
        print(line)
    for line in probes:
        print(line)
    print(f'问题 {len(problems)} 条，probe 行 {len(probes)} 处')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
