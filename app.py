import subprocess
from flask import Flask, request, send_file, jsonify
from io import BytesIO
import tempfile

app = Flask(__name__)

@app.route("/compile", methods=["POST"])
def compile_latex():
    data = request.get_json()
    if not data or "latex" not in data:
        return jsonify({"error": "Send JSON with 'latex' field"}), 400

    latex_code = data["latex"]

    # Use a temporary directory for pdflatex
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = f"{tmpdir}/main.tex"
        pdf_path = f"{tmpdir}/main.pdf"

        with open(tex_path, "w") as f:
            f.write(latex_code)

        try:
            # Run pdflatex twice to resolve references
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-no-shell-escape", "main.tex"],
                    cwd=tmpdir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
        except subprocess.CalledProcessError as e:
            return jsonify({
                "error": "Compilation failed",
                "stdout": e.stdout.decode(),
                "stderr": e.stderr.decode()
            }), 500

        # Read the PDF into memory
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = BytesIO(pdf_file.read())

        pdf_bytes.seek(0)
        return send_file(
            pdf_bytes,
            as_attachment=True,
            download_name="output.pdf",
            mimetype="application/pdf"
        )

@app.route("/")
def index():
    return "LaTeX compiler service running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
