from customer_data_generator import generate_patient_records, generate_patients_csv, PatientRecord


def test_patient_zero(tmp_path):
    out = generate_patients_csv(0, tmp_path / "patients_zero.csv", seed=2)
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("patient_id,")


def test_patient_determinism():
    a = list(generate_patient_records(3, seed=77))
    b = list(generate_patient_records(3, seed=77))
    assert [r.patient_id for r in a] == [r.patient_id for r in b]
    assert all(isinstance(r, PatientRecord) for r in a)


def test_patient_csv(tmp_path):
    out = generate_patients_csv(4, tmp_path / "patients_four.csv", seed=11)
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 5
    header = lines[0].split(',')
    assert 'risk_score' in header
    assert any(';' in l or ',,' in l for l in lines[1:])  # some lists may be empty or joined