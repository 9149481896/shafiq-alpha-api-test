from pathlib import Path
import runpy

# SHAFIQ ALPHA
# Founded & Developed by Magray Shafiq

engine_file = Path(__file__).parent / "upstox_data_engine.py"

if not engine_file.exists():
    raise FileNotFoundError(
        "upstox_data_engine.py not found in repository."
    )

runpy.run_path(
    str(engine_file),
    run_name="__main__"
)
