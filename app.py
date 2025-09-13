import requests
from flask import Flask, request, send_file, jsonify
import tempfile

app = Flask(__name__)

LATEX_CC_URL = "https://latex.cc/api/v1/pdf"

@app.route("/compile", methods=["POST"])
def compile_latex():
    data = request.get_json()
    if not data or "latex" not in data:
        return jsonify({"error": "Send JSON with 'latex' field"}), 400

    latex_code = data["latex"]

    # Call LaTeX.cc API
    try:
        response = requests.post(
            LATEX_CC_URL,
            json={"source": latex_code},
            timeout=30
        )
    except requests.RequestException as e:
        return jsonify({"error": "Failed to reach LaTeX.cc", "details": str(e)}), 500

    if response.status_code != 200:
        return jsonify({"error": "LaTeX.cc compilation failed", "details": response.text}), 500

    # Save PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(response.content)
        tmpfile_path = tmpfile.name

    return send_file(tmpfile_path, as_attachment=True, download_name="output.pdf")

@app.route("/")
def index():
    return "LaTeX.cc compiler service running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
