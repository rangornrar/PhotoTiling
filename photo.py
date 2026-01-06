#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IHM Tkinter : sélectionner une image mosaïque, preview, régler lignes/colonnes,
afficher la grille par-dessus, puis découper en fichiers.

Dépendances :
  pip install pillow

Lancement :
  python split_grid_gui.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


@dataclass
class GridConfig:
    rows: int = 5
    cols: int = 5
    trim: int = 0
    prefix: str = "img"
    fmt: str = "png"


class GridCutterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Découpe mosaïque → photos (preview + grille)")
        self.geometry("1100x750")
        self.minsize(900, 650)

        # State
        self.image_path: Path | None = None
        self.pil_image: Image.Image | None = None  # original
        self.preview_tk: ImageTk.PhotoImage | None = None
        self.preview_scale: float = 1.0  # preview pixels / original pixels
        self.cfg = GridConfig()

        # UI vars
        self.rows_var = tk.IntVar(value=self.cfg.rows)
        self.cols_var = tk.IntVar(value=self.cfg.cols)
        self.trim_var = tk.IntVar(value=self.cfg.trim)
        self.prefix_var = tk.StringVar(value=self.cfg.prefix)
        self.fmt_var = tk.StringVar(value=self.cfg.fmt)

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        # Layout: left controls, right preview
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        left = ttk.Frame(container)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(container)
        right.pack(side="right", fill="both", expand=True)

        # --- Controls ---
        ttk.Label(left, text="Fichier image", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        ttk.Button(left, text="Choisir une image…", command=self.on_choose_image).pack(fill="x")

        self.path_label = ttk.Label(left, text="(aucune image)", wraplength=300)
        self.path_label.pack(anchor="w", pady=(6, 12))

        sep1 = ttk.Separator(left, orient="horizontal")
        sep1.pack(fill="x", pady=8)

        ttk.Label(left, text="Paramètres de grille", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        grid_params = ttk.Frame(left)
        grid_params.pack(fill="x", pady=(0, 8))

        ttk.Label(grid_params, text="Lignes").grid(row=0, column=0, sticky="w")
        rows_spin = ttk.Spinbox(grid_params, from_=1, to=50, textvariable=self.rows_var, width=6, command=self.redraw_grid)
        rows_spin.grid(row=0, column=1, sticky="w", padx=(6, 0))

        ttk.Label(grid_params, text="Colonnes").grid(row=1, column=0, sticky="w", pady=(6, 0))
        cols_spin = ttk.Spinbox(grid_params, from_=1, to=50, textvariable=self.cols_var, width=6, command=self.redraw_grid)
        cols_spin.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0))

        ttk.Label(grid_params, text="Trim (px)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        trim_spin = ttk.Spinbox(grid_params, from_=0, to=50, textvariable=self.trim_var, width=6, command=self.redraw_grid)
        trim_spin.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=(6, 0))

        # Live update if user types
        self.rows_var.trace_add("write", lambda *_: self.redraw_grid())
        self.cols_var.trace_add("write", lambda *_: self.redraw_grid())
        self.trim_var.trace_add("write", lambda *_: self.redraw_grid())

        sep2 = ttk.Separator(left, orient="horizontal")
        sep2.pack(fill="x", pady=8)

        ttk.Label(left, text="Sortie", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        out_params = ttk.Frame(left)
        out_params.pack(fill="x", pady=(0, 8))

        ttk.Label(out_params, text="Préfixe").grid(row=0, column=0, sticky="w")
        ttk.Entry(out_params, textvariable=self.prefix_var).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Label(out_params, text="Format").grid(row=1, column=0, sticky="w", pady=(6, 0))
        fmt_combo = ttk.Combobox(out_params, textvariable=self.fmt_var, values=["png", "jpg", "webp"], state="readonly", width=10)
        fmt_combo.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0))

        out_params.columnconfigure(1, weight=1)

        ttk.Button(left, text="Découper & exporter…", command=self.on_export).pack(fill="x", pady=(10, 0))

        ttk.Label(
            left,
            text="Astuce : si tu as des bordures blanches entre les tuiles,\n"
                 "mets Trim à 1–3 px.",
            foreground="#555",
            wraplength=320,
        ).pack(anchor="w", pady=(10, 0))

        # --- Preview area ---
        ttk.Label(right, text="Preview (grille superposée)", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(right)
        canvas_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.canvas = tk.Canvas(canvas_frame, bg="#111", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        x_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        y_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.grid(row=1, column=0, sticky="ew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas_img_id = None
        self.grid_line_ids: list[int] = []

        # Redraw on resize
        self.bind("<Configure>", lambda e: self._fit_preview_to_canvas())

    # ---------------- Actions ----------------
    def on_choose_image(self) -> None:
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
            ("Tous les fichiers", "*.*"),
        ]
        path_str = filedialog.askopenfilename(title="Choisir une image mosaïque", filetypes=filetypes)
        if not path_str:
            return

        self.image_path = Path(path_str)
        try:
            self.pil_image = Image.open(self.image_path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'image.\n\n{e}")
            self.image_path = None
            self.pil_image = None
            return

        self.path_label.config(text=str(self.image_path))
        self._fit_preview_to_canvas()

    def on_export(self) -> None:
        if self.pil_image is None or self.image_path is None:
            messagebox.showwarning("Info", "Choisis d’abord une image.")
            return

        rows = self._safe_int(self.rows_var.get(), 1)
        cols = self._safe_int(self.cols_var.get(), 1)
        trim = self._safe_int(self.trim_var.get(), 0)
        prefix = self.prefix_var.get().strip() or "img"
        fmt = self.fmt_var.get().strip().lower() or "png"
        if fmt not in {"png", "jpg", "webp"}:
            messagebox.showerror("Erreur", "Format invalide (png/jpg/webp).")
            return

        out_dir_str = filedialog.askdirectory(title="Choisir le dossier de sortie")
        if not out_dir_str:
            return
        out_dir = Path(out_dir_str)

        try:
            count = self.split_grid(self.pil_image, out_dir, rows, cols, trim, prefix, fmt)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec découpe/export.\n\n{e}")
            return

        messagebox.showinfo("OK", f"{count} fichiers exportés dans :\n{out_dir}")

    # ---------------- Core logic ----------------
    @staticmethod
    def split_grid(
        img: Image.Image,
        output_dir: Path,
        rows: int,
        cols: int,
        trim: int,
        prefix: str,
        fmt: str,
    ) -> int:
        output_dir.mkdir(parents=True, exist_ok=True)

        w, h = img.size
        tile_w = w // cols
        tile_h = h // rows

        idx = 1
        for r in range(rows):
            for c in range(cols):
                left = c * tile_w
                upper = r * tile_h
                right = (c + 1) * tile_w if c < cols - 1 else w
                lower = (r + 1) * tile_h if r < rows - 1 else h

                tile = img.crop((left, upper, right, lower))

                if trim > 0:
                    tw, th = tile.size
                    # évite les crop négatifs si trim trop grand
                    t = min(trim, (tw - 1) // 2, (th - 1) // 2)
                    tile = tile.crop((t, t, tw - t, th - t))

                out_path = output_dir / f"{prefix}_{idx:03d}.{fmt}"
                # JPG: évite les surprises de profil couleur
                if fmt == "jpg":
                    tile.save(out_path, quality=95, subsampling=0, optimize=True)
                else:
                    tile.save(out_path)
                idx += 1

        return idx - 1

    # ---------------- Preview drawing ----------------
    def _fit_preview_to_canvas(self) -> None:
        """Redimensionne la preview pour tenir dans la zone visible, puis dessine."""
        if self.pil_image is None:
            self._clear_canvas()
            return

        # Dimensions du canvas visible
        self.update_idletasks()
        cw = max(50, self.canvas.winfo_width())
        ch = max(50, self.canvas.winfo_height())

        iw, ih = self.pil_image.size
        # marge
        cw2, ch2 = cw - 20, ch - 20

        scale = min(cw2 / iw, ch2 / ih, 1.0)
        self.preview_scale = scale

        pw, ph = int(iw * scale), int(ih * scale)
        preview = self.pil_image.resize((pw, ph), Image.LANCZOS)

        self.preview_tk = ImageTk.PhotoImage(preview)

        self.canvas.delete("all")
        self.canvas_img_id = self.canvas.create_image(10, 10, anchor="nw", image=self.preview_tk)

        # Configure scroll region
        self.canvas.config(scrollregion=(0, 0, pw + 20, ph + 20))

        self.redraw_grid()

    def redraw_grid(self) -> None:
        """Redessine la grille selon rows/cols sur l'image preview."""
        if self.pil_image is None or self.canvas_img_id is None:
            return

        # Nettoie anciennes lignes
        for lid in self.grid_line_ids:
            self.canvas.delete(lid)
        self.grid_line_ids.clear()

        rows = self._safe_int(self.rows_var.get(), 1)
        cols = self._safe_int(self.cols_var.get(), 1)

        iw, ih = self.pil_image.size
        scale = self.preview_scale

        pw, ph = int(iw * scale), int(ih * scale)
        x0, y0 = 10, 10
        x1, y1 = x0 + pw, y0 + ph

        # Lignes verticales
        for c in range(1, cols):
            x = x0 + (pw * c) / cols
            lid = self.canvas.create_line(x, y0, x, y1, fill="#00FFB3", width=2)
            self.grid_line_ids.append(lid)

        # Lignes horizontales
        for r in range(1, rows):
            y = y0 + (ph * r) / rows
            lid = self.canvas.create_line(x0, y, x1, y, fill="#00FFB3", width=2)
            self.grid_line_ids.append(lid)

        # Bordure extérieure (pour lecture visuelle)
        self.grid_line_ids.append(self.canvas.create_rectangle(x0, y0, x1, y1, outline="#00FFB3", width=2))

        # Affiche aussi le nombre de tuiles
        total = rows * cols
        self.grid_line_ids.append(
            self.canvas.create_text(
                x0 + 8,
                y0 + 8,
                anchor="nw",
                text=f"{rows}×{cols} = {total} tuiles",
                fill="white",
                font=("Segoe UI", 12, "bold"),
            )
        )

    def _clear_canvas(self) -> None:
        self.canvas.delete("all")
        self.canvas_img_id = None
        self.grid_line_ids.clear()

    @staticmethod
    def _safe_int(value: int, min_value: int) -> int:
        try:
            v = int(value)
        except Exception:
            return min_value
        return max(min_value, v)


if __name__ == "__main__":
    app = GridCutterApp()
    app.mainloop()
