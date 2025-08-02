import os, subprocess, time
from .job_files import write_status, append_log

def run_conversion(job_id, folder, pdf_paths, html_target_dir, stop_event):
    total = len(pdf_paths)
    done = 0

    for pdf_path in pdf_paths:
        # ✅ Cancel-Check ganz am Anfang der Schleife
        if stop_event.is_set():
            append_log(job_id, "Job cancelled by user")
            write_status(
                job_id,
                state="cancelled",
                progress=done / total if total else 0,
                total=total,
                done=done,
                message="cancelled"
            )
            return  # ➡️ Worker beendet sich hier

        # --- deine bisherige Konvertierung ---
        try:
            # PDF zu HTML konvertieren ...
            append_log(job_id, f"Converting {pdf_path}")
            # subprocess / docling call etc.
            done += 1
            write_status(job_id, state="running", progress=done / total, total=total, done=done)
        except Exception as e:
            append_log(job_id, f"Error converting {pdf_path}: {e}")
            write_status(job_id, state="error", progress=done / total, total=total, done=done, message=str(e))
            return

    # ✅ Abschlussstatus nur, wenn nicht abgebrochen
    write_status(job_id, state="done", progress=1.0, total=total, done=done, message="finished")
    append_log(job_id, "All conversions finished")