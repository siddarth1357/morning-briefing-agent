# run_once.py - runs the briefing pipeline once, capturing all output.
# Launched as a detached process so terminal activity can't interrupt it.
import sys
import io

out = io.open("run_output.txt", "w", encoding="utf-8", buffering=1)  # line-buffered
sys.stdout = out
sys.stderr = out

try:
    import main
    main.run_briefing_agent()
except Exception:
    import traceback
    traceback.print_exc()
finally:
    out.close()
