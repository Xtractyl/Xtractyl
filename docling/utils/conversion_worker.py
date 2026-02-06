import os
import subprocess
import time

from .job_files import write_status


def run_conversion(job_id, pdf_paths, html_target_dir, stop_event):
    """
    Convert a list of PDFs to HTML using Docling.
    Progress is written to per-job status files.
    Supports cooperative cancellation via `stop_event`.
    """
    total = len(pdf_paths)
    done = 0

    # Initial status
    write_status(
        job_id,
        state="running",
        progress=0.0 if total else 1.0,
        total=total,
        done=0,
        message="started",
    )

    for pdf_path in pdf_paths:
        # Cancellation check at the start of each iteration
        if stop_event.is_set():
            write_status(
                job_id,
                state="cancelled",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message="cancelled",
            )
            return

        # Convert current PDF
        try:
            # Ensure output directory exists (should already exist, but safe to enforce)
            os.makedirs(html_target_dir, exist_ok=True)

            # Docling CLI call
            # Example: docling input.pdf --from pdf --to html --output /htmls/folder
            cmd = [
                "docling",
                pdf_path,
                "--from",
                "pdf",
                "--to",
                "html",
                "--output",
                html_target_dir,
            ]

            start = time.time()
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            duration = time.time() - start
            done += 1
            progress = (done / total) if total else 1.0

            write_status(
                job_id,
                state="running",
                progress=progress,
                total=total,
                done=done,
                message=f"converted {os.path.basename(pdf_path)} in {duration:.2f}s",
            )

        except subprocess.CalledProcessError as e:
            # Docling failed for this file → mark job as error and stop
            write_status(
                job_id,
                state="error",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message=f"conversion failed (exit={e.returncode})",
            )
            return
        except Exception:
            # Unexpected error → mark job as error and stop
            write_status(
                job_id,
                state="error",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message="unexpected error",
            )
            return

        # Mid-iteration cancellation check (in case stop was requested during conversion)
        if stop_event.is_set():
            write_status(
                job_id,
                state="cancelled",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message="cancelled",
            )
            return

    # Completed all files
    write_status(job_id, state="done", progress=1.0, total=total, done=done, message="finished")
