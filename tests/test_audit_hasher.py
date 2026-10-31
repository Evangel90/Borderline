import json

from audit.hasher import HashChainedLogger


def test_hash_chain_verifies_and_detects_tampering(tmp_path):
    logger = HashChainedLogger(str(tmp_path))
    logger.append({"event": "synthetic incident", "detail": "initial"})
    assert HashChainedLogger.verify_log(logger.log_path)[0] is True

    record = json.loads(open(logger.log_path, encoding="utf-8").read())
    record["detail"] = "changed"
    with open(logger.log_path, "w", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    valid, _, broken_index = HashChainedLogger.verify_log(logger.log_path)
    assert valid is False
    assert broken_index == 0
