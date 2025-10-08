import logging
import os
import subprocess
import time

from .job_files import append_log, write_status

logger = logging.getLogger(__name__)


def run_conversion(job_id, folder, pdf_paths, html_target_dir, stop_event):
    """
    Convert a list of PDFs to HTML using Docling.
    Progress and messages are written to per-job status/log files and also to container logs.
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
    append_log(job_id, f"Started conversion: {total} file(s) in folder '{folder}'")
    logger.info("Job %s: started with %d file(s) → %s", job_id, total, folder)

    for pdf_path in pdf_paths:
        # Cancellation check at the start of each iteration
        if stop_event.is_set():
            append_log(job_id, "Job cancelled by user")
            write_status(
                job_id,
                state="cancelled",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message="cancelled",
            )
            logger.info("Job %s: cancelled at %d/%d", job_id, done, total)
            return

        # Convert current PDF
        try:
            append_log(job_id, f"Converting {pdf_path}")
            logger.info("Job %s: converting %s", job_id, pdf_path)

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
            completed = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            duration = time.time() - start

            # Optional: log Docling stdout/stderr for troubleshooting
            if completed.stdout:
                append_log(job_id, f"docling stdout: {completed.stdout.strip()[:500]}")
            if completed.stderr:
                append_log(job_id, f"docling stderr: {completed.stderr.strip()[:500]}")

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
            append_log(job_id, f"Converted {os.path.basename(pdf_path)} in {duration:.2f}s")
            logger.info(
                "Job %s: converted %s (%.2fs) [%d/%d]", job_id, pdf_path, duration, done, total
            )

        except subprocess.CalledProcessError as e:
            # Docling failed for this file → mark job as error and stop
            msg = (
                f"Docling failed for {os.path.basename(pdf_path)}: {e.stderr or e.stdout or str(e)}"
            )
            append_log(job_id, msg)
            write_status(
                job_id,
                state="error",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message="conversion failed",
            )
            logger.exception("Job %s: %s", job_id, msg)
            return
        except Exception as e:
            # Unexpected error → mark job as error and stop
            msg = f"Unexpected error for {os.path.basename(pdf_path)}: {e}"
            append_log(job_id, msg)
            write_status(
                job_id,
                state="error",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message=str(e),
            )
            logger.exception("Job %s: %s", job_id, msg)
            return

        # Mid-iteration cancellation check (in case stop was requested during conversion)
        if stop_event.is_set():
            append_log(job_id, "Job cancelled by user")
            write_status(
                job_id,
                state="cancelled",
                progress=(done / total) if total else 0.0,
                total=total,
                done=done,
                message="cancelled",
            )
            logger.info("Job %s: cancelled after converting %d/%d", job_id, done, total)
            return

    # Completed all files
    write_status(job_id, state="done", progress=1.0, total=total, done=done, message="finished")
    append_log(job_id, "All conversions finished")
    logger.info("Job %s: finished %d/%d file(s)", job_id, done, total)
