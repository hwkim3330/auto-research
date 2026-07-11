"""Actually executes the LLM-generated experiment code and returns real output.

This is the single most important anti-hallucination lever in this pipeline:
an independent audit found 57% of Sakana AI Scientist v1 manuscripts contained
fabricated numerical results. The paper-writing agent is only ever shown what
was ACTUALLY printed here -- it is never allowed to "estimate" a metric.

SAFETY NOTE: this executes model-generated Python in a subprocess on this
machine with no sandboxing beyond a process timeout. Sakana's own AI Scientist
repo carries the same warning. Do not run this against untrusted topics on a
machine with sensitive data/credentials -- run it in a container or VM if you
want real isolation.
"""
import os
import subprocess
import tempfile


def run_experiment(code, timeout=60):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = subprocess.run(["python3", path], capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-4000:],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": None}
    finally:
        os.unlink(path)
