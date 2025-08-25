# RClone Project
## Overview
Rclone Desktop is a graphical user interface (GUI) application for managing file transfers using Rclone. This application allows users to easily download files from various remote storage services using a simple and intuitive interface.

<!-- ## Project structure
```text
rclone/                  # project folder
├─ .venv/                # virtual environment (ignored in git)
├─ app.py            # Python code
├─ requirements.txt      # pip packages
└─ README.md             # setup instructions
``` -->

## Project Structure
```text
rclone-desktop/
├── src/
│   └── app.py                  # Main application code for the Rclone desktop app
|   └── img/
|       └── rclone_logo_icon.png    # Desktop app icon
├── appimage-builder.yml            # Configuration file for AppImage Builder
├── rclone.desktop                  # Desktop entry file for the application
├── AppRun                          # Entry point script for the AppImage
├── requirements.txt                # Python dependencies required for the project
├── .vscode/
│   └── settings.json               # VS Code settings for the project
├── .venv/                          # Virtual envirnment files
├── .gitignore                      # Files and directories to ignore in Git
└── README.md                       # Documentation for the project
```


## Installation Instructions

### 1. Install System Dependencies
Ensure you have the necessary system dependencies installed:
```bash
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 libcairo2-dev pkg-config build-essential libgirepository1.0-dev
```

### 2. Set Up Your Environment
Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```
   (**currently it's empty, Skip this step**)

### 4. Build the AppImage
Follow these steps to create the AppImage:
1. Ensure you have AppImage tools installed:
   ```bash
   sudo apt install appimage-builder
   ```
2. Make the `AppRun` script executable:
   ```bash
   chmod +x AppRun
   ```
3. Run the AppImage Builder command:
   ```bash
   appimage-builder
   ```

### 5. Test the AppImage
After building, you can find the AppImage in the output directory. Make it executable and run it:
```bash
chmod +x RcloneDesktop-0.2-x86_64.AppImage
./RcloneDesktop-0.2-x86_64.AppImage
```

## Usage
To run the application, simply execute the generated AppImage file. The GUI will allow you to manage file transfers using Rclone seamlessly.
