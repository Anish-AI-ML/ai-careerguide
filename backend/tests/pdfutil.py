def make_pdf(pages: list[list[str]]) -> bytes:
    """Minimal text PDF builder for tests."""
    esc = lambda s: s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")  # noqa: E731
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for i, lines in enumerate(pages):
        pid, cid = 4 + 2 * i, 5 + 2 * i
        kids.append(f"{pid} 0 R")
        body = "BT /F1 10 Tf 40 760 Td 12 TL\n" + "\n".join(f"({esc(l)}) Tj T*" for l in lines) + "\nET"
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {cid} 0 R /Resources << /Font << /F1 3 0 R >> >> >>".encode())
        objs.append(f"<< /Length {len(body)} >>\nstream\n{body}\nendstream".encode())
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    return out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode()


GOOD = ["Jane Doe", "Education", "B.E. Computer Science (AI and ML), Example Institute, CGPA 8.4", "Skills",
        "Python, TensorFlow, Machine Learning, Deep Learning, SQL, Git, Docker, Pandas, AWS",
        "Projects", "Traffic Flow Prediction",
        "- Built a machine learning model using Python and TensorFlow reaching 92% accuracy on 120,000 records",
        "- Deployed the model with Docker on AWS and reduced inference time by 40%",
        "Sentiment Analyzer", "- Developed an NLP classifier with Pandas and SQL pipelines for 5,000 reviews",
        "Experience", "Machine Learning Intern", "- Implemented data pipelines in Python and SQL, improved data quality by 30%",
        "- Designed evaluation dashboards and presented results to the team",
        "Certifications", "Deep Learning Specialization", "Hackathons", "Winner, college AI hackathon 2025"]
WEAK = ["John Smith", "Objective", "Looking for a job where I can grow and learn new things in a good company.",
        "Skills", "Microsoft Word, teamwork", "Hobbies", "Reading books and listening to music in the evening hours daily."]
