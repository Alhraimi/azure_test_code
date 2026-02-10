# Build Instructions

## Important Note

**You CANNOT build a Windows `.exe` file on macOS.**  
**You CANNOT build a macOS `.app` file on Windows.**

The executable you build will match the operating system you are running the command on.  
To get a Windows `.exe`, you must copy this project folder to a Windows machine (or virtual machine) and run the build command there.

## Running on Windows

1.  **Install Python**: Download and install Python 3.9+ from python.org. Make sure to check "Add Python to PATH" during installation.
2.  **Open Project Folder**: Navigate to this folder.
3.  **Run Build Script**: Double-click `build_windows.bat`.
    *   This will automatically install dependencies and create the `.exe`.
4.  **Find Your App**: The executable will be in the `dist` folder named `InspirationApp.exe`.

## Running on macOS

1.  **Install Xcode Tools** (required for PyInstaller):
    Open Terminal and run:
    ```bash
    xcode-select --install
    ```
    (Follow the prompts to install)

2.  **Build App**:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --name "InspirationApp" app.py
    ```

3.  **Find Your App**: The application will be in the `dist` folder named `InspirationApp.app`.

## Troubleshooting

-   **"Command not found"**: Ensure Python is added to your system PATH.
-   **Anti-Virus blocking**: Sometimes Windows Defender flags new unsigned `.exe` files. This is normal for self-built apps. Add an exclusion if necessary.
