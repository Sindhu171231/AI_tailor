import tempfile, subprocess, os
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

@app.route("/compile", methods=["POST"])
def compile_latex():
    data = request.get_json()
    if not data or "latex" not in data:
        return jsonify({"error": "Send JSON with 'latex' field"}), 400

    latex_code = data["latex"]
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "main.tex")
        pdf_path = os.path.join(tmpdir, "main.pdf")
        with open(tex_path, "w") as f:
            f.write(latex_code)

        # Run pdflatex
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                cwd=tmpdir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "Compilation failed", "log": e.stdout.decode()}), 500

        return send_file(pdf_path, as_attachment=True, download_name="output.pdf")

@app.route("/")
def index():
    return "LaTeX compiler service running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
