
import io
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from fpdf import FPDF
from PIL import Image

logger = logging.getLogger(__name__)

# ── Paleta VigorDAE ────────────────────────────────────────────────────────────
COLOR_VERDE  = (39, 174, 96)
COLOR_NARANJA = (224, 123, 84)
COLOR_AMARILLO = (242, 201, 76)
COLOR_GRIS   = (100, 100, 100)
COLOR_NEGRO  = (30, 30, 30)
COLOR_FONDO  = (245, 248, 245)


class VigorDAEReport(FPDF):
    """Subclase FPDF con header/footer corporativos."""

    def __init__(self, lote_id: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.lote_id = lote_id
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(left=20, top=15, right=20)

    def header(self):
        # Barra verde superior
        self.set_fill_color(*COLOR_VERDE)
        self.rect(0, 0, 210, 12, "F")
        # Título en blanco
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 2)
        self.cell(0, 8, "AgroIA · VigorDAE  —  Sistema de Monitoreo Satelital Inteligente", ln=False)
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLOR_GRIS)
        self.cell(0, 5, f"Lote: {self.lote_id}  |  Página {self.page_no()}  |  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C")

    # ── Helpers de estilo ──────────────────────────────────────────────────────
    def section_title(self, title: str) -> None:
        self.ln(4)
        self.set_fill_color(*COLOR_FONDO)
        self.set_draw_color(*COLOR_VERDE)
        self.set_line_width(0.5)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COLOR_NEGRO)
        self.cell(0, 8, f"  {title}", border="L", fill=True, ln=True)
        self.ln(2)

    def kpi_row(self, items: list[tuple[str, str]]) -> None:
        """Fila de KPIs: lista de (label, valor)."""
        col_w = (self.w - 40) / len(items)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*COLOR_GRIS)
        for label, _ in items:
            self.cell(col_w, 5, label, align="C")
        self.ln(5)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*COLOR_NEGRO)
        for _, valor in items:
            self.cell(col_w, 8, valor, align="C")
        self.ln(10)

    def info_table(self, rows: list[tuple[str, str]]) -> None:
        """Tabla de dos columnas: etiqueta / valor."""
        col_label = 60
        col_valor = self.w - 40 - col_label
        self.set_font("Helvetica", "", 10)
        for label, valor in rows:
            self.set_fill_color(250, 250, 250)
            self.set_text_color(*COLOR_GRIS)
            self.cell(col_label, 7, label, border="B", fill=True)
            self.set_text_color(*COLOR_NEGRO)
            self.set_font("Helvetica", "B", 10)
            self.cell(col_valor, 7, str(valor) if valor else "—", border="B", ln=True)
            self.set_font("Helvetica", "", 10)
        self.ln(4)


# ── Función principal ──────────────────────────────────────────────────────────

def generate_report(
    lote_id: str,
    df_resumen: pd.DataFrame,
    zonas_data: list[dict],
    fenologia: dict | None,
    mapa_png_bytes: bytes | None,
    titulo: str = "Informe de Campaña",
    region: str = "Córdoba, Argentina",
) -> bytes:
    """
    Genera el PDF completo y retorna los bytes para descarga.
    """
    pdf = VigorDAEReport(lote_id=lote_id)
    pdf.add_page()

    # ── 1. Portada / Cabecera ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*COLOR_NEGRO)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_GRIS)
    pdf.cell(0, 6, f"Lote: {lote_id}  ·  {region}", ln=True, align="C")
    pdf.cell(0, 6, f"Fecha de generación: {datetime.now().strftime('%d de %B de %Y')}", ln=True, align="C")
    pdf.ln(6)

    # ── 2. KPIs globales ───────────────────────────────────────────────────────
    pdf.section_title("Resumen del Lote")

    ndvi_max  = round(float(df_resumen["ndvi_auditado"].max()), 3)
    ndvi_prom = round(float(df_resumen["ndvi_auditado"].mean()), 3)
    n_anom    = int(df_resumen["es_anomalia"].sum())
    pct_anom  = round(n_anom / len(df_resumen) * 100, 1)
    n_fechas  = len(df_resumen)

    pdf.kpi_row([
        ("NDVI Máximo", str(ndvi_max)),
        ("NDVI Promedio", str(ndvi_prom)),
        ("Imágenes procesadas", str(n_fechas)),
        ("Anomalías corregidas", f"{n_anom} ({pct_anom}%)"),
    ])

    # ── 3. Gráfico NDVI global ─────────────────────────────────────────────────
    pdf.section_title("Serie Temporal NDVI — Crudo vs Auditado")
    chart_png = _plot_ndvi_series(df_resumen)
    if chart_png:
        _embed_image(pdf, chart_png, w=170)
    pdf.ln(4)

    # ── 4. Zonificación ────────────────────────────────────────────────────────
    pdf.section_title("Zonificación de Manejo")

    if zonas_data:
        zona_colores = {
            "Bajo":  COLOR_NARANJA,
            "Medio": (200, 160, 50),
            "Alto":  COLOR_VERDE,
        }
        col_w = (pdf.w - 40) / 3
        pdf.set_font("Helvetica", "B", 10)
        for zona in zonas_data:
            nombre = zona.get("nombre", f"Zona {zona['zona']}")
            pct    = zona.get("pct_pixeles") or 0
            color  = zona_colores.get(nombre, COLOR_GRIS)
            pdf.set_fill_color(*color)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(col_w, 10, f"{nombre}  {pct}%", align="C", fill=True, border=1)
        pdf.ln(12)

        # Gráfico comparativo de zonas
        chart_zonas = _plot_zonas(zonas_data)
        if chart_zonas:
            _embed_image(pdf, chart_zonas, w=170)
        pdf.ln(4)

    # ── 5. Mapa de zonificación ────────────────────────────────────────────────
    if mapa_png_bytes:
        pdf.section_title("Mapa de Zonificación Espacial")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COLOR_GRIS)
        pdf.cell(0, 5, "Naranja = Bajo vigor  ·  Amarillo = Medio  ·  Verde = Alto  ·  Gris = Sin dato", ln=True, align="C")
        pdf.ln(2)
        _embed_image(pdf, mapa_png_bytes, w=120, center=True)
        pdf.ln(4)

    # ── 6. Fenología ───────────────────────────────────────────────────────────
    pdf.section_title("Análisis Fenológico")
    if fenologia:
        def _fmt_date(d):
            if d is None: return "—"
            try: return pd.to_datetime(d).strftime("%d/%m/%Y")
            except: return str(d)

        pdf.info_table([
            ("Inicio de campaña",  _fmt_date(fenologia.get("inicio"))),
            ("Pico de vigor",      _fmt_date(fenologia.get("pico"))),
            ("Fin estimado",       _fmt_date(fenologia.get("fin"))),
            ("Duración (días)",    str(fenologia.get("duracion_dias", "—"))),
        ])

    # ── 7. Notas finales ───────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*COLOR_GRIS)
    pdf.multi_cell(
        0, 5,
        "Este informe fue generado automáticamente por AgroIA - VigorDAE. "
        "Los datos de NDVI han sido auditados por el Agente Verificador (LSTM Autoencoder) "
        "para garantizar la integridad ecofisiológica. La zonificación fue realizada mediante K-Means.",
        align="J"
    )

    return bytes(pdf.output())


def _plot_ndvi_series(df: pd.DataFrame) -> bytes | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, ax = plt.subplots(figsize=(10, 3.5))
        fig.patch.set_facecolor("#F5F8F5")
        ax.set_facecolor("#F5F8F5")

        fechas = pd.to_datetime(df["time"])
        ax.plot(fechas, df["ndvi_raw"],      color="#AAAAAA", lw=1,   ls="--", label="NDVI Crudo")
        ax.plot(fechas, df["ndvi_auditado"], color="#1A7A4A", lw=2,   label="NDVI Auditado (DAE)")

        ax.set_ylim(-0.05, 1.0)
        ax.set_ylabel("NDVI", fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        ax.legend(fontsize=8, loc="upper left")
        ax.spines[["top", "right"]].set_visible(False)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except: return None


def _plot_zonas(zonas_data: list[dict]) -> bytes | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        colores = {"Bajo": "#E07B54", "Medio": "#C8A832", "Alto": "#27AE60"}
        fig, ax = plt.subplots(figsize=(10, 3.5))
        fig.patch.set_facecolor("#F5F8F5")
        ax.set_facecolor("#F5F8F5")

        for zona in zonas_data:
            df_z  = pd.DataFrame(zona["data"])
            fechas = pd.to_datetime(df_z["time"])
            nombre = zona.get("nombre", f"Zona {zona['zona']}")
            color  = colores.get(nombre, "#888888")
            ax.plot(fechas, df_z["ndvi"], color=color, lw=2, label=nombre)

        ax.set_ylim(-0.05, 1.0)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        ax.legend(fontsize=8, loc="upper left")
        ax.spines[["top", "right"]].set_visible(False)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except: return None


def _embed_image(pdf: FPDF, img_bytes: bytes, w: float = 160, center: bool = False) -> None:
    try:
        buf = io.BytesIO(img_bytes)
        x = (pdf.w - w) / 2 if center else pdf.get_x()
        pdf.image(buf, x=x, w=w)
    except: pass
