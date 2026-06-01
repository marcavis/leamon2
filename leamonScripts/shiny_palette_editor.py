#!/usr/bin/env python3
"""Interactive palette editor for creating shiny.pal files.

Usage:
  ./shiny_palette_editor.py

Workflow:
  1) Load sprite image (PNG).
  2) Load matching normal.pal (JASC-PAL).
  3) Edit palette colors in hex fields or with color picker.
  4) See live 4x swapped preview.
  5) Export shiny.pal with same color order.
"""

from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from check_sprite_colors import parse_png_rgba_pixels, write_jasc_palette, write_rgba_png

RgbColor = tuple[int, int, int]
RgbaColor = tuple[int, int, int, int]


def parse_jasc_palette(path: Path) -> list[RgbColor]:
    lines = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError("Palette file is too short")
    if lines[0] != "JASC-PAL" or lines[1] != "0100":
        raise ValueError("Palette file is not JASC-PAL 0100 format")

    count = int(lines[2])
    if len(lines) < 3 + count:
        raise ValueError("Palette declares more colors than provided")

    colors: list[RgbColor] = []
    for line in lines[3 : 3 + count]:
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"Invalid palette line: {line!r}")
        r, g, b = (int(parts[0]), int(parts[1]), int(parts[2]))
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError(f"Palette value out of range: {line!r}")
        colors.append((r, g, b))

    return colors


def rgb_to_hex(rgb: RgbColor) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def hex_to_rgb(value: str) -> RgbColor:
    s = value.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        raise ValueError("Expected 6 hex digits")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def color_distance_sq(a: RgbColor, b: RgbColor) -> int:
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return dr * dr + dg * dg + db * db


class PaletteEditorApp:
    def __init__(self, root: tk.Tk, initial_image: Path | None = None, initial_palette: Path | None = None) -> None:
        self.root = root
        self.root.title("Shiny Palette Editor")

        self.scale = 4
        self.image_path: Path | None = None
        self.palette_path: Path | None = None

        self.width = 0
        self.height = 0
        self.pixels: list[RgbaColor] = []
        self.pixel_indices: list[int] = []

        self.normal_palette: list[RgbColor] = []
        self.edited_palette: list[RgbColor] = []

        self.original_preview_image: tk.PhotoImage | None = None
        self.edited_preview_image: tk.PhotoImage | None = None

        self.palette_vars: list[tk.StringVar] = []
        self.palette_entries: list[ttk.Entry] = []
        self.update_after_id: str | None = None

        self.status_var = tk.StringVar(value="Load image and normal.pal to begin")

        self._build_ui()

        if initial_image:
            self.load_image(initial_image)
        if initial_palette:
            self.load_palette(initial_palette)

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Load Image", command=self.prompt_image).pack(side="left")
        ttk.Button(toolbar, text="Load normal.pal", command=self.prompt_palette).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Export shiny.pal", command=self.export_palette).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Export preview PNG", command=self.export_preview_png).pack(side="left", padx=(8, 0))

        previews = ttk.Frame(self.root, padding=(8, 4, 8, 8))
        previews.pack(fill="both", expand=True)
        previews.columnconfigure(0, weight=1)
        previews.columnconfigure(1, weight=1)

        left_box = ttk.LabelFrame(previews, text="Original", padding=6)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        right_box = ttk.LabelFrame(previews, text="Edited (live swap)", padding=6)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.original_preview = ttk.Label(left_box)
        self.original_preview.pack(anchor="center")

        self.edited_preview = ttk.Label(right_box)
        self.edited_preview.pack(anchor="center")

        controls = ttk.LabelFrame(self.root, text="Palette Entries", padding=8)
        controls.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.palette_scroll_canvas = tk.Canvas(controls, height=260, highlightthickness=0)
        self.palette_scroll_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(controls, orient="vertical", command=self.palette_scroll_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.palette_scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self.palette_frame = ttk.Frame(self.palette_scroll_canvas)
        self.palette_scroll_canvas.create_window((0, 0), window=self.palette_frame, anchor="nw")
        self.palette_frame.bind(
            "<Configure>",
            lambda _e: self.palette_scroll_canvas.configure(scrollregion=self.palette_scroll_canvas.bbox("all")),
        )

        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(8, 0, 8, 8))
        status_bar.pack(fill="x")

    def prompt_image(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select sprite PNG",
            filetypes=[("PNG images", "*.png"), ("All files", "*")],
        )
        if selected:
            self.load_image(Path(selected))

    def prompt_palette(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select normal.pal",
            filetypes=[("Palette files", "*.pal"), ("All files", "*")],
        )
        if selected:
            self.load_palette(Path(selected))

    def load_image(self, path: Path) -> None:
        try:
            width, height, pixels = parse_png_rgba_pixels(path)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load image:\n{exc}")
            return

        visible_colors = {pixel[:3] for pixel in pixels if pixel[3] > 0}
        if len(visible_colors) > 16:
            messagebox.showerror(
                "Too many colors",
                f"Image has {len(visible_colors)} visible colors.\nThis tool expects up to 16.",
            )
            return

        self.image_path = path.resolve()
        self.width = width
        self.height = height
        self.pixels = pixels
        self.status_var.set(f"Loaded image: {self.image_path}")

        if self.palette_path is None:
            guess = self.image_path.with_name("normal.pal")
            if guess.exists():
                self.load_palette(guess)

        self.rebuild_indices()
        self.refresh_previews()

    def load_palette(self, path: Path) -> None:
        try:
            palette = parse_jasc_palette(path)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load palette:\n{exc}")
            return

        if len(palette) == 0:
            messagebox.showerror("Error", "Palette has no entries")
            return

        self.palette_path = path.resolve()
        self.normal_palette = palette
        self.edited_palette = palette[:]
        self.status_var.set(f"Loaded normal.pal: {self.palette_path}")

        self._rebuild_palette_editors()
        self.rebuild_indices()
        self.refresh_previews()

    def _rebuild_palette_editors(self) -> None:
        for child in self.palette_frame.winfo_children():
            child.destroy()

        self.palette_vars.clear()
        self.palette_entries.clear()

        if not self.normal_palette:
            ttk.Label(self.palette_frame, text="Load normal.pal to edit colors").grid(row=0, column=0, sticky="w")
            return

        ttk.Label(self.palette_frame, text="Idx", width=4).grid(row=0, column=0, sticky="w")
        ttk.Label(self.palette_frame, text="Hex Color", width=12).grid(row=0, column=1, sticky="w")
        ttk.Label(self.palette_frame, text="", width=10).grid(row=0, column=2, sticky="w")

        for idx, rgb in enumerate(self.edited_palette):
            ttk.Label(self.palette_frame, text=str(idx), width=4).grid(row=idx + 1, column=0, sticky="w", pady=1)

            var = tk.StringVar(value=rgb_to_hex(rgb))
            var.trace_add("write", self._on_palette_text_changed)
            entry = ttk.Entry(self.palette_frame, textvariable=var, width=12)
            entry.grid(row=idx + 1, column=1, sticky="w", padx=(0, 6), pady=1)

            pick_btn = ttk.Button(self.palette_frame, text="Pick", command=lambda i=idx: self.pick_color(i))
            pick_btn.grid(row=idx + 1, column=2, sticky="w", pady=1)

            self.palette_vars.append(var)
            self.palette_entries.append(entry)

    def pick_color(self, index: int) -> None:
        if not (0 <= index < len(self.palette_vars)):
            return
        current = self.palette_vars[index].get()
        initial = current if current.startswith("#") else f"#{current}"
        _rgb, hex_color = colorchooser.askcolor(color=initial, parent=self.root)
        if hex_color:
            self.palette_vars[index].set(hex_color.upper())

    def _on_palette_text_changed(self, *_args: object) -> None:
        if self.update_after_id is not None:
            self.root.after_cancel(self.update_after_id)
        self.update_after_id = self.root.after(80, self._apply_palette_edits)

    def _apply_palette_edits(self) -> None:
        self.update_after_id = None
        if not self.palette_vars:
            return

        next_palette: list[RgbColor] = []
        bad_indices: list[int] = []

        for idx, var in enumerate(self.palette_vars):
            text = var.get().strip()
            try:
                rgb = hex_to_rgb(text)
                next_palette.append(rgb)
                self.palette_entries[idx].configure(style="TEntry")
            except Exception:
                bad_indices.append(idx)
                self.palette_entries[idx].configure(style="Invalid.TEntry")

        if bad_indices:
            self.status_var.set(f"Invalid color at index(es): {', '.join(map(str, bad_indices))}")
            return

        self.edited_palette = next_palette
        self.status_var.set("Palette updated")
        self.refresh_previews()

    def rebuild_indices(self) -> None:
        if not self.pixels or not self.normal_palette:
            self.pixel_indices = []
            return

        palette_to_index = {rgb: idx for idx, rgb in enumerate(self.normal_palette)}
        nearest_fallbacks = 0

        indices: list[int] = []
        for pixel in self.pixels:
            if pixel[3] == 0:
                indices.append(0)
                continue

            rgb = pixel[:3]
            if rgb in palette_to_index:
                indices.append(palette_to_index[rgb])
            else:
                nearest = min(range(len(self.normal_palette)), key=lambda i: color_distance_sq(rgb, self.normal_palette[i]))
                indices.append(nearest)
                nearest_fallbacks += 1

        self.pixel_indices = indices
        if nearest_fallbacks > 0:
            self.status_var.set(
                f"Loaded with {nearest_fallbacks} non-exact pixel matches (mapped to nearest palette entries)"
            )

    def refresh_previews(self) -> None:
        if not self.pixels:
            return

        if self.normal_palette and self.pixel_indices:
            original_pixels = self.render_with_palette(self.normal_palette)
            edited_pixels = self.render_with_palette(self.edited_palette or self.normal_palette)
        else:
            original_pixels = self.flatten_original_pixels()
            edited_pixels = original_pixels

        self.original_preview_image = self.make_photoimage(original_pixels)
        self.edited_preview_image = self.make_photoimage(edited_pixels)
        self.original_preview.configure(image=self.original_preview_image)
        self.edited_preview.configure(image=self.edited_preview_image)

    def flatten_original_pixels(self) -> list[RgbColor]:
        out: list[RgbColor] = []
        for px in self.pixels:
            if px[3] == 0:
                out.append(self.checker_at(len(out) % self.width, len(out) // self.width))
            else:
                out.append((px[0], px[1], px[2]))
        return out

    def checker_at(self, x: int, y: int) -> RgbColor:
        tile = ((x // 2) + (y // 2)) % 2
        return (176, 176, 176) if tile == 0 else (136, 136, 136)

    def render_with_palette(self, palette: list[RgbColor]) -> list[RgbColor]:
        out: list[RgbColor] = []
        for i, px in enumerate(self.pixels):
            x = i % self.width
            y = i // self.width
            if px[3] == 0:
                out.append(self.checker_at(x, y))
                continue

            idx = self.pixel_indices[i] if i < len(self.pixel_indices) else 0
            idx = max(0, min(idx, len(palette) - 1))
            out.append(palette[idx])
        return out

    def make_photoimage(self, rgb_pixels: list[RgbColor]) -> tk.PhotoImage:
        scaled_w = self.width * self.scale
        scaled_h = self.height * self.scale

        rows = bytearray()
        for y in range(self.height):
            row = rgb_pixels[y * self.width : (y + 1) * self.width]
            expanded = bytearray()
            for r, g, b in row:
                expanded.extend((r, g, b) * self.scale)
            for _ in range(self.scale):
                rows.extend(expanded)

        header = f"P6\n{scaled_w} {scaled_h}\n255\n".encode("ascii")
        ppm = header + bytes(rows)
        return tk.PhotoImage(data=ppm, format="PPM")

    def export_palette(self) -> None:
        if not self.edited_palette:
            messagebox.showerror("Error", "No edited palette to export")
            return

        initial_dir = self.palette_path.parent if self.palette_path else Path.cwd()
        target = filedialog.asksaveasfilename(
            title="Export shiny.pal",
            defaultextension=".pal",
            initialdir=initial_dir,
            initialfile="shiny.pal",
            filetypes=[("Palette files", "*.pal"), ("All files", "*")],
        )
        if not target:
            return

        target_path = Path(target)
        try:
            write_jasc_palette(target_path, self.edited_palette)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to export palette:\n{exc}")
            return

        self.status_var.set(f"Exported {target_path}")
        messagebox.showinfo("Export complete", f"Wrote {target_path}")

    def render_swapped_rgba(self) -> list[RgbaColor]:
        if not self.pixels or not self.edited_palette:
            return []

        out: list[RgbaColor] = []
        for i, px in enumerate(self.pixels):
            if px[3] == 0:
                out.append((0, 0, 0, 0))
                continue

            idx = self.pixel_indices[i] if i < len(self.pixel_indices) else 0
            idx = max(0, min(idx, len(self.edited_palette) - 1))
            rgb = self.edited_palette[idx]
            out.append((rgb[0], rgb[1], rgb[2], px[3]))
        return out

    def export_preview_png(self) -> None:
        if not self.pixels or not self.edited_palette:
            messagebox.showerror("Error", "Load image and palette first")
            return

        if self.image_path is not None:
            initial_dir = self.image_path.parent
            initial_name = f"{self.image_path.stem}_shiny_preview.png"
        else:
            initial_dir = Path.cwd()
            initial_name = "shiny_preview.png"

        target = filedialog.asksaveasfilename(
            title="Export shiny preview PNG",
            defaultextension=".png",
            initialdir=initial_dir,
            initialfile=initial_name,
            filetypes=[("PNG images", "*.png"), ("All files", "*")],
        )
        if not target:
            return

        target_path = Path(target)
        try:
            rgba_pixels = self.render_swapped_rgba()
            write_rgba_png(target_path, self.width, self.height, rgba_pixels)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to export preview:\n{exc}")
            return

        self.status_var.set(f"Exported preview {target_path}")
        messagebox.showinfo("Export complete", f"Wrote {target_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Edit normal.pal colors and export shiny.pal")
    parser.add_argument("image", nargs="?", type=Path, help="Optional sprite PNG to load on startup")
    parser.add_argument("--pal", type=Path, help="Optional normal.pal to load on startup")
    args = parser.parse_args()

    root = tk.Tk()
    style = ttk.Style(root)
    style.configure("Invalid.TEntry", fieldbackground="#FFD8D8")

    app = PaletteEditorApp(root, args.image, args.pal)
    if app.image_path is None and args.image is not None:
        messagebox.showwarning("Startup", f"Could not load image: {args.image}")
    if app.palette_path is None and args.pal is not None:
        messagebox.showwarning("Startup", f"Could not load palette: {args.pal}")

    root.minsize(780, 640)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
