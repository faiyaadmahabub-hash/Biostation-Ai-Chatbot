# Local verification — 17 October 2026

Environment: Windows, Python 3.10.9. Existing system Flask/pandas/numpy/Ollama-client/ChromaDB/sentence-transformers installations were used. This is not a clean install of the pinned requirements. R 4.4.2 was found at `C:\Program Files\R\R-4.4.2\bin\Rscript.exe`; `rpy2` was absent. Ollama service/model replies were not tested.

## Reproduce the scoped smoke check

From the repository root:

```powershell
$env:USE_TF='0'
$env:USE_FLAX='0'
python -u docs/verify_local.py
```

Result: exit 0. The script uses disposable synthetic data and temporary SQLite files. It exercises real application code, not mocked routes or an LLM.

| Check | Result |
|---|---|
| Home page | HTTP 200 |
| Four-row/two-column synthetic CSV upload and preview | Passed |
| Dataset session retrieval | Passed |
| Conversation create/read/delete | Passed |
| Built-in R template generation | 21/21 |
| Built-in R-code export | 20/21 HTTP 200; `correlation_matrix` HTTP 404 |
| `/api/run-code` with base R only | Passed; synthetic mean 2.5, plot produced |
| LLM, semantic retrieval, automatic repair | Not exercised |

The 404 follows the export route's advisor-knowledge lookup: the loader has a correlation-matrix template that the advisor catalog does not expose. It is recorded rather than silently counted as a passing export. No production source was changed.

## Existing test suite

Installed pytest 9.1.1 into a task-specific external folder, not the project or global environment:

```powershell
python -m pip install --target C:/Users/ajakd/.t3/scratch/readme-work/ai-verification-deps pytest
$env:PYTHONPATH='C:/Users/ajakd/.t3/scratch/readme-work/ai-verification-deps'
python -m pytest tests/unit/test_error_parser.py -q
```

Result: **4 failed**, exit 1. Tests expect snake-case error types while the parser returns display names; one expects a missing `severity` field; a nonnumeric-warning example matches the parser's earlier missing-values pattern. These are existing failures; the smoke result is not a claim that the entire test suite passes. The integration suite was not run because it requires absent fixtures and model services and has a stale app-factory signature.

## Image provenance

[synthetic-r-check.jpg](assets/synthetic-r-check.jpg) is the actual JPEG produced by the successful `/api/run-code` synthetic `plot(x, x^2)` request. It was copied from ignored `data/plots/` after the run. No private data, model output or rendered terminal image is involved.

The real Flask server was also started on `http://127.0.0.1:8111` with `create_app('production')`, debug/reloader disabled. T3 `preview_open` reached the BioStation page; `preview_snapshot(save:true)` timed out twice after 15 seconds, so no UI screenshot is claimed.

## Remaining prerequisites and limits

- Install/start Ollama and obtain the configured model before testing interpretation or model-assisted routing.
- Verify optional semantic retrieval and fresh dependency installation separately. Heavy optional ML imports delayed startup locally; disabling TensorFlow/Flax imports reduced unrelated startup work.
- Install required CRAN packages before exercising statistical templates. This check used base R and did not install CRAN packages or evaluate the template catalog statistically.
- Existing routing, HTML-rendering and arbitrary-code-execution concerns remain in the [project guide](PROJECT_GUIDE.md). Use trusted local input on loopback.
