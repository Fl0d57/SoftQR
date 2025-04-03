# -----------------------------------------------------------------------------
# SoftQR - Open Source QR Code Generator Application
#
# Developer: Rahian BEDROUNI
# Date: April 2025
#
# This application is an open-source project for generating customizable QR codes.
# -----------------------------------------------------------------------------

import os
from flask import Flask, request, send_file, render_template_string, jsonify
import qrcode
from PIL import Image
import tempfile
import json
import threading
import tkinter as tk
from tkinter import filedialog
import webview
import queue

file_save_queue = queue.Queue()

app = Flask(__name__)

# Global variable to store the uploaded logo file
logo_file_path = None

# Default parameters
default_params = {
    "qr_color": "#463d35",
    "bg_color": "#ffffff",
    "transparent_bg": False
}

@app.route('/temp-file', methods=['GET'])
def get_temp_file():
    temp_file = request.args.get('file')
    if not temp_file or not os.path.exists(temp_file):
        return jsonify({"error": "Temporary file not found"}), 404
    return send_file(temp_file, mimetype='image/png')

@app.route('/download', methods=['POST'])
def download_qr():
    temp_file = request.json.get('temp_file')
    if not temp_file or not os.path.exists(temp_file):
        return jsonify({"error": "Temporary QR code file not found"}), 400

    try:
        # Execute in the main thread
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            title="Save QR Code As"
        )
        root.destroy()  # Properly close the Tkinter instance

        if save_path:
            with open(temp_file, 'rb') as src:
                with open(save_path, 'wb') as dst:
                    dst.write(src.read())
            os.remove(temp_file)  # Clean up the temp file
            return jsonify({"message": f"QR Code saved successfully at {save_path}"})
        else:
            return jsonify({}), 200  # User canceled the save operation

    except Exception as e:
        print(f"Error during QR code download: {e}")
        return jsonify({"error": "Failed to save QR code"}), 500

@app.route('/generate', methods=['POST'])
def generate_qr():
    global logo_file_path
    text = request.form.get('text', '').strip()
    qr_color = request.form.get('qr_color', default_params['qr_color'])
    bg_color = request.form.get('bg_color', default_params['bg_color'])
    transparent_bg = request.form.get('transparent_bg') == 'on'
    logo = request.files.get('logo')
    logo_size_percentage = int(request.form.get('logo_size', 50))  # Default 50%
    qr_padding_percentage = int(request.form.get('qr_size', 20))  # Default 20% padding

    if not text:
        return jsonify({"error": "Text field is empty"}), 400

    try:
        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,  # Fixed box size
            border=0,  # No default border
        )
        qr.add_data(text)
        qr.make(fit=True)

        qr_code = qr.make_image(fill_color=qr_color, back_color="transparent" if transparent_bg else bg_color).convert('RGBA')
        qr_width, qr_height = qr_code.size  # Get QR dimensions

        # Calculate padding in pixels
        padding_pixels = int((qr_width * qr_padding_percentage) / 100)
        total_size = qr_width + (2 * padding_pixels)

        # Create a new image with padding
        qr_img = Image.new('RGBA', (total_size, total_size), (255, 255, 255, 0) if transparent_bg else bg_color)

        # **Center QR code inside the new image**
        qr_position = ((total_size - qr_width) // 2, (total_size - qr_height) // 2)
        qr_img.paste(qr_code, qr_position)

        # If a logo is provided, add it
        if logo:
            logo_file_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            logo.save(logo_file_path)

            logo_img = Image.open(logo_file_path).convert("RGBA")
            logo_size = int((total_size * logo_size_percentage) / 100)  # Scale logo relative to full image size
            logo_img = logo_img.resize((logo_size, logo_size))

            # **Center logo inside the padded QR image**
            logo_position = ((total_size - logo_size) // 2, (total_size - logo_size) // 2)
            qr_img.paste(logo_img, logo_position, logo_img)

        # Save QR code temporarily
        qr_img_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        qr_img.save(qr_img_path)

        return jsonify({"temp_file": qr_img_path})

    except Exception as e:
        print(f"Error during QR generation: {e}")
        return jsonify({"error": "Failed to generate QR code"}), 500



@app.route('/')
def index():
    return render_template_string('''
<html>
    <head>
        <style>
            /* General Styles */
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                padding: 20px;
                transition: background-color 0.3s, color 0.3s;
            }
            body.dark-mode {
                background-color: #2c2c2c;
                color: #f4f4f9;
            }
            .container {
                max-width: 600px;
                margin: auto;
                background: #fff;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                transition: background 0.3s;
            }
            .container.dark-mode {
                background: #444;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            }
            h1 { text-align: center; color: #333; }
            h1.dark-mode { color: #f4f4f9; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; color: #333; }
            label.dark-mode { color: #f4f4f9; }
            input, button {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 5px;
            }
            input.dark-mode {
                background: #333;
                color: #f4f4f9;
                border: 1px solid #666;
            }
            input[type="color"] {
                height: 40px;
                cursor: pointer;
            }
            button, input[type="submit"] {
                background-color: #463d35;
                color: #fff;
                cursor: pointer;
            }
            button:hover, input[type="submit"]:hover {
                background-color: #5e4a42;
            }
            .switch {
                position: relative;
                display: inline-block;
                width: 50px;
                height: 25px;
                margin: 20px auto;
            }
            .switch input { display: none; }
            .slider {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                border-radius: 25px;
                transition: 0.4s;
            }
            .slider:before {
                content: "";
                position: absolute;
                height: 19px;
                width: 19px;
                bottom: 3px;
                left: 3px;
                background-color: #fff;
                border-radius: 50%;
                transition: 0.4s;
            }
            input:checked + .slider { background-color: #463d35; }
            input:checked + .slider:before { transform: translateX(25px); }
            #qrResult {
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                padding: 20px 0;
            }
            #qrResult img {
                max-width: 100%;
                height: auto;
            }
        </style>
    </head>
    <body onload="loadDarkMode()">
        <div class="container">
            <h1>QR Code Generator</h1>
            <!-- Dark Mode Switch -->
            <label class="switch">
                <input type="checkbox" id="darkModeSwitch" onclick="toggleDarkMode()">
                <span class="slider"></span>
            </label>
            <!-- Form -->
            <form id="qrForm" onsubmit="generateQR(event)" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="text">Text:</label>
                    <input type="text" name="text" id="text">
                </div>
                <div class="form-group">
                    <label for="logo">Logo:</label>
                    <div style="display: flex; align-items: center;">
                        <input type="file" name="logo" id="logo">
                        <button type="button" id="removeLogoButton" onclick="removeLogo()"
                            style="margin-left: 10px; background: transparent; border: none; color: black; cursor: pointer; font-size: 18px;">✖</button>
                    </div>
                </div>
                <div class="form-group">
                    <label for="logo_size">Logo Size:</label>
                    <input type="range" name="logo_size" id="logo_size" min="10" max="100" value="50" onchange="updateLabel('logo_size_label', this.value)">
                    <span id="logo_size_label">50%</span>
                </div>
                <div class="form-group">
                    <label for="qr_size">QR Padding (%):</label>
                    <input type="range" name="qr_size" id="qr_size" min="0" max="100" value="20" step="1" onchange="updateLabel('qr_size_label', this.value)">
                    <span id="qr_size_label">20%</span>
                </div>
                <div class="form-group">
                    <label for="qr_color">QR Color:</label>
                    <input type="color" name="qr_color" id="qr_color" value="#463d35">
                </div>
                <div class="form-group">
                    <label for="bg_color">Background Color:</label>
                    <input type="color" name="bg_color" id="bg_color" value="#ffffff">
                </div>
                <div class="form-group">
                    <label for="transparent_bg">Transparent Background:</label>
                    <input type="checkbox" name="transparent_bg" id="transparent_bg">
                </div>
                <input type="submit" value="Generate QR">
            </form>
            <!-- QR Result -->
            <div id="qrResult"></div>
            <!-- Download and Copy Buttons -->
            <button onclick="downloadQR()">Download QR</button>
            <button onclick="copyQR()">Copy QR Image</button>
        </div>
        <!-- Scripts -->
        <script>
        let tempFilePath = null;

            function generateQR(event) {
                event.preventDefault();
                const formData = new FormData(document.getElementById('qrForm'));

                fetch('/generate', { method: 'POST', body: formData })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            alert(data.error); // Only show alert for errors
                        } else {
                            tempFilePath = data.temp_file; // Store the temp file path
                            const img = document.createElement('img');
                            img.src = `/temp-file?file=${encodeURIComponent(data.temp_file)}`;
                            img.id = 'generatedQR';
                            img.style.display = 'block';
                            img.style.margin = 'auto';  // Ensure it's centered

                            const resultDiv = document.getElementById('qrResult');
                            resultDiv.innerHTML = ''; // Clear previous results
                            resultDiv.appendChild(img); // Add the new QR code
                        }
                    })
                    .catch(() => alert('Error generating QR code'));
            }

            // Update QR code when sliders change
            document.getElementById('logo_size').addEventListener('input', generateQR);
            document.getElementById('qr_size').addEventListener('input', generateQR);

            function downloadQR() {
                if (!tempFilePath) {
                    console.error('No QR code available to download');
                    return;
                }

                fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ temp_file: tempFilePath })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            console.error(data.error); // Log error silently
                        } else {
                            console.log('Download successful or canceled by the user'); // Log silently
                        }
                    })
                    .catch(() => console.error('Error downloading QR code'));
            }

            // Copy QR Code to Clipboard
            async function copyQR() {
                const img = document.getElementById('generatedQR');
                if (img) {
                    const response = await fetch(img.src);
                    const blob = await response.blob();
                    const item = new ClipboardItem({ 'image/png': blob });
                    await navigator.clipboard.write([item]);
                } else {
                    alert('No QR code to copy');
                }
            }

            // Toggle Dark Mode
            function toggleDarkMode() {
                const darkMode = document.body.classList.toggle('dark-mode');
                document.querySelector('.container').classList.toggle('dark-mode');
                document.querySelectorAll('h1, label').forEach(el => el.classList.toggle('dark-mode'));
                localStorage.setItem('darkMode', darkMode ? 'enabled' : 'disabled');

                // Change the "X" button color based on the mode
                const removeButton = document.getElementById('removeLogoButton');
                if (darkMode) {
                    removeButton.style.color = '#f4f4f9'; // Light color for dark mode
                } else {
                    removeButton.style.color = 'black'; // Dark color for light mode
                }
            }

            // Load Dark Mode from Storage
            function loadDarkMode() {
                const isDarkMode = localStorage.getItem('darkMode') === 'enabled';
                if (isDarkMode) {
                    toggleDarkMode();
                    document.getElementById('darkModeSwitch').checked = true;

                    // Adjust button color on load if dark mode is enabled
                    const removeButton = document.getElementById('removeLogoButton');
                    removeButton.style.color = '#f4f4f9';
                }
            }


            // Function to remove the selected image
                function removeLogo() {
                    const logoInput = document.getElementById('logo');
                    logoInput.value = ''; // Clears the input field
                    alert('Logo image has been removed.');
                }

        </script>
    </body>
</html>

    ''', default_params=default_params)  # Pass default_params to the template


def start_server():
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)

def start_application():
    webview.create_window("SoftQR", "http://localhost:8000")
    webview.start()

if __name__ == '__main__':
    # Load default parameters from file if it exists
    if os.path.exists('default_params.json'):
        with open('default_params.json', 'r') as f:
            default_params = json.load(f)

    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Start Tkinter window or browser window for the application
    start_application()
