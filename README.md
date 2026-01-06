# Grid Image Cutter – User Guide

## Overview
Grid Image Cutter is a Python desktop application with a Tkinter GUI that allows you to split a mosaic image into a grid.  
You can preview the image, overlay a grid, adjust rows, columns and trim margins, then export each tile as an individual image file.

Typical use cases:
- Splitting photo mosaics
- Preparing datasets for AI / ML
- Cutting spritesheets or tiled images

---

## Requirements

### Operating System
- Windows, macOS, or Linux

### Software
- **Python 3.9 or newer** (recommended: 3.10+)

### Python Dependencies
- Pillow

---

## Installation

### 1. Install Python
Download and install Python from:
https://www.python.org/downloads/

During installation on Windows:
- ✔ Check “Add Python to PATH”

Verify installation:
```bash
python --version
```

### 2. Install dependencies
Open a terminal / command prompt and run:
```bash
pip install pillow
```

### 3. Application file
Place the script file (e.g. `split_grid_gui.py`) in a directory of your choice.

---

## Launching the Application

From the application directory:
```bash
python split_grid_gui.py
```

The graphical interface will open automatically.

---

## User Interface Overview

### Left Panel – Controls
- **Choose image**: Select the source mosaic image
- **Grid parameters**:
  - Rows: number of horizontal tiles
  - Columns: number of vertical tiles
  - Trim (px): removes border pixels inside each tile
- **Output settings**:
  - Prefix: filename prefix for exported images
  - Format: png, jpg, or webp
- **Export**: splits and saves the images

### Right Panel – Preview
- Scaled preview of the image
- Grid overlay showing tile boundaries
- Automatic refresh when parameters change

---

## How Grid Splitting Works

- The image is divided evenly by rows and columns
- Edge tiles automatically adapt if dimensions are not perfectly divisible
- Trim removes pixels from all sides of each tile to eliminate borders or seams

Example:
```
Rows: 5
Columns: 5
Result: 25 output images
```

---

## Export Behavior

- Output files are named:
```
<prefix>_001.png
<prefix>_002.png
...
```
- JPEG export uses high quality (95%) and no subsampling
- Output directory is created automatically if needed

---

## Tips & Best Practices

- Use **Trim = 1–3 px** if you see white lines between tiles
- Prefer **PNG** for lossless workflows
- Use **JPG** for smaller files when quality loss is acceptable
- Large images are automatically scaled for preview, without affecting export quality

---

## Troubleshooting

**Application does not start**
- Check Python version
- Ensure Pillow is installed

**Grid not visible**
- Verify rows/columns are greater than 0
- Resize the window to refresh preview

**Unexpected crop**
- Reduce trim value
- Verify grid size matches the mosaic layout

---

## License / Usage
This tool is intended for local, offline use.  
You are free to modify and integrate it into your own workflows.

---

Happy slicing.
