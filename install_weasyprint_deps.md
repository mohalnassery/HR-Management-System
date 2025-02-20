# Installing WeasyPrint Dependencies on Windows

Follow these steps to install the required GTK dependencies for WeasyPrint:

1. Download and install MSYS2:
   - Go to https://www.msys2.org/
   - Download the installer (msys2-x86_64-*.exe)
   - Run the installer and follow the installation steps
   - Use default installation path (C:\msys64)

2. Install GTK3 and required dependencies:
   - Open "MSYS2 MINGW64" from Start Menu
   - Run these commands:
   ```bash
   pacman -Syu
   pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python-pip mingw-w64-x86_64-gcc mingw-w64-x86_64-gobject-introspection mingw-w64-x86_64-cairo mingw-w64-x86_64-pkg-config mingw-w64-x86_64-python3
   ```

3. Add GTK binary location to system PATH:
   - Open System Properties (Win + R, type sysdm.cpl)
   - Click "Environment Variables"
   - Under "System Variables" find "Path"
   - Click "Edit"
   - Add new entry: C:\msys64\mingw64\bin
   - Click "OK" to save
   
4. Verify the installation:
   - Open a new Command Prompt
   - Run: `python -c "import weasyprint; weasyprint.HTML('http://weasyprint.org/').write_pdf('weasyprint.pdf')"`
   - If successful, it will create a PDF file

Now WeasyPrint should work correctly with all required GTK dependencies installed.

## Troubleshooting

If you encounter issues:

1. Ensure you've restarted your terminal/IDE after modifying PATH
2. Verify GTK installation:
   ```bash
   pkg-config --libs-only-l gtk+-3.0
   ```
3. Check if gobject is available:
   ```bash
   python -c "from weasyprint.text.ffi import ffi, gobject"
   ```

For more detailed troubleshooting, refer to:
https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows