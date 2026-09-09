from __future__ import annotations

import json
import os
import subprocess
import sys


def test_runtime_config_does_not_load_parent_dotenv(tmp_path):
    (tmp_path / ".env").write_text("OPENAI_MODEL=parent-project-model\n")
    child = tmp_path / "questionnaire-experiment"
    child.mkdir()
    (child / ".env").write_text("OPENAI_MODEL=questionnaire-model\n")
    env = dict(os.environ)
    for key in ("OPENAI_MODEL", "QUESTIONNAIRE_HOME", "API_DATABASE_PATH", "PYTHONPATH"):
        env.pop(key, None)
    result = subprocess.run(
        [sys.executable, "-c", (
            "import json; from rscb_questionnaire.settings import settings; "
            "print(json.dumps([settings.OPENAI_MODEL, str(settings.API_DATABASE_PATH)]))"
        )],
        cwd=child,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == [
        "questionnaire-model", str(child / "data" / "questionnaire-security.db")
    ]
    (child / ".env").unlink()
    result = subprocess.run(
        [sys.executable, "-c", (
            "from rscb_questionnaire.settings import settings; print(settings.OPENAI_MODEL)"
        )],
        cwd=child,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() != "parent-project-model"
