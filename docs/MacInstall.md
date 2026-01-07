# Mac Install Plan

## Goals
- Add macOS-friendly wrapper scripts under `service_scripts/` for create/install/start/shutdown/restart.
- Keep Windows and Ubuntu flows unchanged by only adding new macOS scripts.

## Prerequisites
- macOS with a working Python 3 interpreter (`python3` or `python` on PATH).
- (Optional) Set `PYTHON_BIN` if you need a specific interpreter for venv creation.

## Plan
1. Create the venv:
   - `service_scripts/mac_create_venv.sh`
   - Uses `VENV_PATH` (default: `.venv`) and respects `PYTHON_BIN`.
2. Install dependencies:
   - `service_scripts/mac_install.sh`
   - Runs `service_scripts/install_with_venv.py` inside the venv and preloads the Docling model from `DOCLING_MODEL_NAME` (macOS/Windows).
3. Start the service:
   - `service_scripts/mac_start.sh`
   - Uses `API_HOST`, `API_PORT`, and `UVICORN_RELOAD` from the environment.
4. Shutdown the service:
   - `service_scripts/mac_shutdown.sh`
   - Uses `PIDFILE`, `PROCESS_MATCH`, and `SHUTDOWN_TIMEOUT` if set.
5. Restart the service:
   - `service_scripts/mac_restart.sh`
   - Uses `RESTART_DELAY` along with shutdown options.
6. Run the end-to-end test:
   - `service_scripts/mac_system_test.sh`
   - Calls all of the above scripts, waits for `/health`, and writes logs to `data/`.
   - Uses `API_HOST`/`API_PORT` from the environment if set; otherwise reads `.env`/`.env.local.example` before choosing a free port.

## Test Inputs (Optional)
- `VENV_PATH=.venv`
- `API_HOST=127.0.0.1`
- `PORT_START=18081`
- `PORT_COUNT=10`

## Example Run
```
./service_scripts/mac_system_test.sh
```

## Notes From mac_system_test
- First install downloads the Docling model from Hugging Face; expect extra install time and network usage.
- The Docling runtime may still download additional assets (for example `ds4sd/docling-models`) on first start.
- The restart log may show a `multiprocessing/resource_tracker` leaked semaphore warning on shutdown; test still passes and the service stops cleanly.
