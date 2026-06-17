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
