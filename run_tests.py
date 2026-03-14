import os
from datetime import datetime
import subprocess

timestamp = datetime.now().strftime("%d-%m-%Y--%H-%M")

os.makedirs("Reports", exist_ok=True)

report_path = os.path.join(
    "Reports",
    f"Cflow-Automation-Report-CI-CD--{timestamp}.html"
)

subprocess.run(
    [
        "pytest",
        f"--html={report_path}",
        "--self-contained-html"
    ],
    check=True
)