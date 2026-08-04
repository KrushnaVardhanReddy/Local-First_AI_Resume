import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

def update_tracker(job, match, output_dir: Path) -> None:
    """
    Read existing `tracker.md` and `tracker.csv` if present;
    find row by (company, title) key; update in place or append new row
    with columns: Company, Title, Location, Match Score, Salary, Link, Resume, Status;
    new entries have `Status = "- [ ]"`;
    write both files atomically (write to temp file, then rename)
    """
    tracker_md_path = output_dir / "tracker.md"
    tracker_csv_path = output_dir / "tracker.csv"

    headers = ["Company", "Title", "Location", "Match Score", "Salary", "Link", "Resume", "Status"]

    rows = []
    if tracker_csv_path.exists():
        with open(tracker_csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                pass
            for row in reader:
                rows.append(row)

    company = job.company
    title = job.title

    found = False
    for row in rows:
        if row.get("Company") == company and row.get("Title") == title:
            row["Location"] = job.location
            row["Match Score"] = str(match.score) if match else ""

            if job.salary_min is not None and job.salary_max is not None:
                salary = f"{job.salary_min}-{job.salary_max}"
            elif job.salary_min is not None:
                salary = str(job.salary_min)
            elif job.salary_max is not None:
                salary = str(job.salary_max)
            else:
                salary = ""
            row["Salary"] = salary
            row["Link"] = job.source_url
            row["Resume"] = f"output/{job.slug}/resume.pdf"
            found = True
            break

    if not found:
        if job.salary_min is not None and job.salary_max is not None:
            salary = f"{job.salary_min}-{job.salary_max}"
        elif job.salary_min is not None:
            salary = str(job.salary_min)
        elif job.salary_max is not None:
            salary = str(job.salary_max)
        else:
            salary = ""

        rows.append({
            "Company": company,
            "Title": title,
            "Location": job.location,
            "Match Score": str(match.score) if match else "",
            "Salary": salary,
            "Link": job.source_url,
            "Resume": f"output/{job.slug}/resume.pdf",
            "Status": "- [ ]"
        })

    with NamedTemporaryFile(mode='w', delete=False, dir=output_dir, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            clean_row = {k: row.get(k, "") for k in headers}
            writer.writerow(clean_row)
        temp_csv = f.name

    os.replace(temp_csv, tracker_csv_path)

    with NamedTemporaryFile(mode='w', delete=False, dir=output_dir, encoding='utf-8') as f:
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
        for row in rows:
            clean_row = [str(row.get(k, "")) for k in headers]
            f.write("| " + " | ".join(clean_row) + " |\n")
        temp_md = f.name

    os.replace(temp_md, tracker_md_path)
