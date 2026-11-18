import json

from assay_protocol_validator.cli import main


def test_cli_json_output_for_valid_protocol(capsys) -> None:
    exit_code = main(["examples/valid_elisa.yaml", "--json"])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["protocol_name"] == "cytokine_elisa"
    assert output["status"] == "valid"
    assert output["errors"] == []


def test_cli_json_output_for_invalid_protocol(capsys) -> None:
    exit_code = main(["examples/invalid_well.yaml", "--json"])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "invalid"
    assert output["errors"][0]["code"] == "INVALID_WELL"
    assert "not valid for plate type" in output["errors"][0]["message"]


def test_fix_cli_shows_proposal_and_preserves_source(tmp_path, capsys):
    from pathlib import Path

    source = Path("examples/evaluation/pcr_setup_unknown_reagent.yaml").read_bytes()
    path = tmp_path / "protocol.yaml"
    path.write_bytes(source)
    assert main(["fix", str(path)]) == 0
    output = capsys.readouterr().out
    assert "Outcome: accepted" in output
    assert "demo_setup_mxi" in output
    assert "Candidate validation" in output
    assert "Status: VALID" in output
    assert path.read_bytes() == source


def test_fix_cli_requests_human_input(capsys):
    assert main(["fix", "examples/evaluation/pcr_setup_cumulative_shortage.yaml", "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "request_human_input"
    assert result["edit"] is None
