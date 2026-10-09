"""Run each unittest module in a fresh, bounded process for Qt fixture isolation."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]

def execute(module, timeout, output):
    started = time.monotonic()
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONUTF8='1')
    env['MASTIXA_TEST_TIMEOUT'] = str(timeout)
    with tempfile.TemporaryDirectory(prefix='mastixa-test-') as directory:
        env['MASTIXA_DATA_HOME'] = directory
        process = subprocess.Popen([sys.executable, '-m', 'tools.run_test_module', module], cwd=ROOT,
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        timed_out = False
        try:
            raw, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.kill()
            raw, _ = process.communicate(timeout=10)
    text = raw.decode('utf-8', errors='replace')
    if output:
        (output / (module + '.log')).write_text(text, encoding='utf-8')
    match = re.search(r'^Ran (\d+) tests?', text, re.MULTILINE)
    cases = re.findall(r'^(?:FAIL|ERROR): (.+)$', text, re.MULTILINE)
    return {'module': module, 'status': 'TIMEOUT' if timed_out else ('PASS' if process.returncode == 0 else 'FAIL'),
            'exit_code': process.returncode, 'tests': int(match[1]) if match else None,
            'timeout_seconds': timeout, 'elapsed_seconds': round(time.monotonic() - started, 3),
            'failed_cases': cases, 'summary': text[-6000:] if process.returncode else ''}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=1)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--module-timeout', action='append', default=[], metavar='MODULE=SECONDS',
                        help='Explicit bound for a measured heavyweight module; all other modules keep --timeout')
    parser.add_argument('--output', type=Path)
    parser.add_argument('modules', nargs='*')
    args = parser.parse_args()
    if args.timeout < 10:
        parser.error('Timeout must be at least 10 seconds')
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
    modules = args.modules or ['tests.' + p.stem for p in sorted((ROOT/'tests').glob('test_*.py'))]
    bounds = {}
    for override in args.module_timeout:
        name, separator, value = override.partition('=')
        if not separator or name not in modules or not value.isdecimal() or int(value) < 10:
            parser.error('Module timeout must name a selected module and an integer bound >= 10')
        if name in bounds:
            parser.error('Duplicate module timeout: ' + name)
        bounds[name] = int(value)
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [executor.submit(execute, m, bounds.get(m, args.timeout), args.output) for m in modules]
        for future in futures:
            result = future.result()
            results.append(result)
            print(f"{result['status']}: {result['module']} ({result['tests']} tests)", flush=True)
            if result['status'] != 'PASS':
                print(result['summary'], flush=True)
    report = {'modules': results, 'tests': sum(r['tests'] or 0 for r in results),
              'passed_modules': sum(r['status'] == 'PASS' for r in results),
              'failed_modules': sum(r['status'] != 'PASS' for r in results)}
    if args.output:
        (args.output/'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Modules: {len(results)}; passed: {report['passed_modules']}; blocked: {report['failed_modules']}; tests completed: {report['tests']}")
    raise SystemExit(bool(report['failed_modules']))
