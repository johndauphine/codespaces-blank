import subprocess, sys, json, os, shutil
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "simple_data_gen.py"
PY = sys.executable


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_no_arg_defaults(tmp_path, monkeypatch):
    # Copy script into tmp_path to avoid clobbering repo CSV
    target = tmp_path / "simple_data_gen.py"
    target.write_text(SCRIPT.read_text())
    # Provide a src/ package copy (symlink or copy)
    src_src = Path(__file__).resolve().parent.parent / 'src'
    shutil.copytree(src_src, tmp_path / 'src')
    r = run([PY, str(target)])
    assert r.returncode == 0, r.stderr
    # Extract written path from stdout
    line = r.stdout.strip().splitlines()[-1]
    # Expect format: Wrote 100 customer records -> /path/to/customers.csv
    assert 'customer records -> ' in line
    out_path = Path(line.split('->',1)[1].strip())
    assert out_path.exists()
    lines = out_path.read_text().strip().splitlines()
    # header + 100 rows expected by default
    assert len(lines) == 101
    assert lines[0].startswith('customer_id,')


def test_both_mode(tmp_path):
    target = tmp_path / "simple_data_gen.py"
    target.write_text(SCRIPT.read_text())
    src_src = Path(__file__).resolve().parent.parent / 'src'
    shutil.copytree(src_src, tmp_path / 'src')
    out_dir = tmp_path / 'out'
    r = run([PY, str(target), 'both', '5', str(out_dir), '--prefix', 'demo_'])
    assert r.returncode == 0, r.stderr
    cust = out_dir / 'demo_customers.csv'
    pat = out_dir / 'demo_patients.csv'
    assert cust.exists() and pat.exists()
    cust_lines = cust.read_text().strip().splitlines()
    pat_lines = pat.read_text().strip().splitlines()
    assert len(cust_lines) == 6  # header + 5
    assert len(pat_lines) == 6
    assert cust_lines[0].startswith('customer_id,')
    assert pat_lines[0].startswith('patient_id,')
