from customer_data_generator import generate_customer_records, generate_customers_csv, CustomerRecord


def test_generate_zero(tmp_path):
    out = generate_customers_csv(0, tmp_path / "zero.csv", seed=1)
    content = out.read_text().strip().splitlines()
    assert len(content) == 1  # header only
    header_cols = content[0].split(",")
    assert "customer_id" in header_cols


def test_record_count_and_determinism():
    recs1 = list(generate_customer_records(5, seed=123))
    recs2 = list(generate_customer_records(5, seed=123))
    assert [r.customer_id for r in recs1] == [r.customer_id for r in recs2]
    assert len(recs1) == 5
    assert all(isinstance(r, CustomerRecord) for r in recs1)


def test_csv_written(tmp_path):
    out = generate_customers_csv(3, tmp_path / "three.csv", seed=9)
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 4  # header + 3 rows
    assert lines[0].startswith("customer_id,")
