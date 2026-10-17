"""Exercise real local routes with disposable synthetic data; never calls an LLM."""
import io
import logging
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix="biostation-check-") as temporary:
        os.chdir(temporary)
        from config import Config
        base = Path(temporary)
        Config.UPLOAD_FOLDER = base / "data/uploads"
        Config.LOG_FILE = base / "data/logs/app.log"
        Config.SQLITE_DB_PATH = base / "data/database/chats.db"
        Config.CHROMA_DB_PATH = base / "data/chroma"
        from app import create_app
        app = create_app("production")
        app.config["TESTING"] = True
        client = app.test_client()
        assert client.get("/").status_code == 200
        print("PASS home renders")
        response = client.post("/api/upload", data={"file": (io.BytesIO(
            b"group,response\ncontrol,1\ncontrol,2\ntreatment,3\ntreatment,4\n"
        ), "synthetic.csv")}, content_type="multipart/form-data")
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["rows"] == 4
        assert client.get("/api/dataset-info").get_json()["success"]
        print("PASS synthetic CSV upload, preview and dataset session (4 rows, 2 columns)")
        conversation = client.post("/api/conversations", json={"title": "Synthetic smoke check"})
        identifier = conversation.get_json()["conversation_id"]
        assert client.get(f"/api/conversations/{identifier}").get_json()["success"]
        assert client.delete(f"/api/conversations/{identifier}").get_json()["success"]
        print("PASS create, read and delete conversation")
        from app.code_gen.template_loader import TemplateLoader
        loader = TemplateLoader()
        unavailable = []
        for test in loader.TEMPLATE_MAP:
            code = loader.generate_code(test, "synthetic.csv")
            assert 'read.csv("synthetic.csv")' in code, test
            status = client.get(f"/api/export/r-code/{test}").status_code
            if status != 200:
                unavailable.append((test, status))
        print(f"PASS {len(loader.TEMPLATE_MAP)} built-in templates generate (R not executed)")
        print(f"EXPORT {len(loader.TEMPLATE_MAP) - len(unavailable)} successful; unavailable={unavailable}")
        from app.r_engine import r_executor
        if not r_executor.available:
            result = client.post("/api/run-code", json={"code": "print(1 + 1)"}).get_json()
            assert result["success"] is False and "not available" in result["error"]
            print("CONFIRMED BLOCKER R unavailable; API reports failure explicitly")
        else:
            result = client.post("/api/run-code", json={"code":
                'x <- c(1,2,3,4); cat("synthetic_mean=", mean(x), "\\n"); '
                'plot(x, x^2, main="Synthetic base-R smoke check")'
            }).get_json()
            assert result["success"], result
            assert "2.5" in result["output"], result
            assert result["plots"], result
            print("PASS actual R subprocess via /api/run-code: synthetic mean 2.5 and plot produced")
        print("LLM and semantic retrieval not exercised; no model replies fabricated")
        logging.shutdown()
        os.chdir(ROOT)


if __name__ == "__main__":
    main()
