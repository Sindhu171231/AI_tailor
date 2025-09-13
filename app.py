import subprocess
from flask import Flask, request, send_file, jsonify
from io import BytesIO
import tempfile
import os

app = Flask(__name__)

@app.route("/compile", methods=["POST"])
def compile_latex():
    """
    Compiles LaTeX code received as raw text in a POST request body
    and returns the resulting PDF.
    """
    # Get raw LaTeX code from the request body.
    # 'request.get_data(as_text=True)' reads the body of the request as a string.
    latex_code = request.get_data(as_text=True)

    if not latex_code:
        return jsonify({"error": "Request body is empty. Please send LaTeX code as raw text."}), 400

    # Use a temporary directory to store the .tex, .pdf, and other auxiliary files.
    # The 'with' statement ensures the directory and its contents are cleaned up afterward.
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_filename = "main.tex"
        pdf_filename = "main.pdf"
        log_filename = "main.log"
        
        tex_path = os.path.join(tmpdir, tex_filename)
        pdf_path = os.path.join(tmpdir, pdf_filename)
        log_path = os.path.join(tmpdir, log_filename)

        # Write the received LaTeX code to a .tex file.
        # Using utf-8 encoding is important for handling special characters.
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)

        try:
            # Run pdflatex twice. The first run generates auxiliary files
            # (like .aux, .toc), and the second run uses them to resolve
            # cross-references, table of contents, etc.
            for i in range(2):
                # The 'subprocess.run' command executes pdflatex.
                subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode", # Prevents pdflatex from stopping on errors.
                        "-no-shell-escape",         # Disables shell commands for security.
                        tex_filename
                    ],
                    cwd=tmpdir,        # Run the command in the temporary directory.
                    check=True,        # Raise CalledProcessError if pdflatex returns a non-zero exit code.
                    capture_output=True # Capture stdout and stderr.
                )
        except subprocess.CalledProcessError:
            # If compilation fails, read the log file which contains detailed error info.
            log_content = ""
            if os.path.exists(log_path):
                 with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                    log_content = log_file.read()

            # Return a detailed error response.
            return jsonify({
                "error": "LaTeX compilation failed.",
                "log": log_content, # The log file is the most useful for debugging LaTeX.
            }), 500

        # Check if the PDF file was created successfully.
        if not os.path.exists(pdf_path):
             log_content = ""
             if os.path.exists(log_path):
                 with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                    log_content = log_file.read()
             return jsonify({
                "error": "PDF file not created. Check logs for details.",
                "log": log_content
             }), 500


        # Read the compiled PDF file into a memory buffer.
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = BytesIO(pdf_file.read())

        pdf_bytes.seek(0)
        
        # Send the PDF back to the client.
        return send_file(
            pdf_bytes,
            as_attachment=True,
            download_name="output.pdf",
            mimetype="application/pdf"
        )

@app.route("/")
def index():
    """A simple index route to show the service is running."""
    return "LaTeX compiler service is running. POST your raw LaTeX code to the /compile endpoint."

if __name__ == "__main__":
    # Note: For production, use a proper WSGI server like Gunicorn or uWSGI.
    app.run(host="0.0.0.0", port=5000)
