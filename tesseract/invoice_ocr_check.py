import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import List, Tuple, Optional

try:
    from PIL import Image
except ImportError:
    print("Pillow no está instalado. Instala con: pip install Pillow", file=sys.stderr)
    raise

try:
    import pytesseract
except ImportError:
    print("pytesseract no está instalado. Instala con: pip install pytesseract", file=sys.stderr)
    raise

# Configuración de la ruta de Tesseract para Windows.
# Puedes sobrescribirla con la variable de entorno TESSERACT_PATH si lo prefieres.
DEFAULT_TESSERACT_PATH = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
TESSERACT_PATH = os.environ.get("TESSERACT_PATH", DEFAULT_TESSERACT_PATH)

def configure_tesseract() -> None:
    if os.name == "nt":
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        if not os.path.isfile(pytesseract.pytesseract.tesseract_cmd):
            print(
                f"Advertencia: No se encontró Tesseract en '{pytesseract.pytesseract.tesseract_cmd}'.\n"
                "Instálalo y/o ajusta la variable TESSERACT_PATH.",
                file=sys.stderr,
            )

def load_image(image_path: str) -> Image.Image:
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"No se encontró la imagen: {image_path}")
    return Image.open(image_path)

def ocr_extract_text(image: Image.Image) -> str:
    # Intentar con español; fallback a inglés
    config = "--psm 6"
    try:
        text = pytesseract.image_to_string(image, lang="spa", config=config)
        if text.strip():
            return text
    except pytesseract.TesseractError:
        pass
    return pytesseract.image_to_string(image, lang="eng", config=config)

def normalize_amount_str(raw: str) -> Optional[Decimal]:
    """
    Convierte cadenas numéricas (con . y ,) a Decimal(2).
    Heurística:
    - Si hay ambos separadores (.,), el último es decimal.
    - Si solo hay coma y termina en ,dd → coma decimal.
    - Si solo hay punto y termina en .dd → punto decimal.
    - Separadores de miles se eliminan.
    """
    s = raw.strip()
    s = re.sub(r"[\s\$€£¥₡₱₲₵₴₹₽₺]", "", s)
    if not s:
        return None

    comma = "," in s
    dot = "." in s

    try:
        if comma and dot:
            last_sep = max(s.rfind(","), s.rfind("."))
            decimal_sep = s[last_sep]
            thousand_sep = "," if decimal_sep == "." else "."
            s_clean = s.replace(thousand_sep, "")
            s_clean = s_clean.replace(decimal_sep, ".")
            value = Decimal(s_clean)
        elif comma and not dot:
            if re.search(r",\d{2}$", s):
                s_clean = s.replace(".", "")
                s_clean = s_clean.replace(",", ".")
                value = Decimal(s_clean)
            else:
                s_clean = s.replace(",", "")
                value = Decimal(s_clean)
        elif dot and not comma:
            if re.search(r"\.\d{2}$", s):
                parts = s.split(".")
                if len(parts) > 2:
                    s_clean = "".join(parts[:-1]) + "." + parts[-1]
                else:
                    s_clean = s
                value = Decimal(s_clean)
            else:
                s_clean = s.replace(".", "")
                value = Decimal(s_clean)
        else:
            value = Decimal(s)

        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None

def extract_amounts_from_text(text: str) -> Tuple[List[Decimal], List[Tuple[int, Decimal]], Optional[Decimal]]:
    """
    Devuelve:
    - amounts_all: montos candidatos a ítems (excluyendo líneas del total)
    - amounts_with_line_index: (line_index, monto) para referencia
    - total_amount: total detectado (si existe)
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    money_regex = re.compile(r"(?:[\$€£¥])?\s*([+-]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})|[+-]?\d+[\.,]\d{2})")
    keywords_total = re.compile(r"\b(total|importe\s*total|total\s*a\s*pagar|gran\s*total)\b", re.IGNORECASE)

    amounts_with_line_index: List[Tuple[int, Decimal]] = []
    totals_found: List[Decimal] = []

    for idx, line in enumerate(lines):
        if keywords_total.search(line):
            for m in money_regex.finditer(line):
                val = normalize_amount_str(m.group(1))
                if val is not None:
                    totals_found.append(val)
        for m in money_regex.finditer(line):
            val = normalize_amount_str(m.group(1))
            if val is not None:
                amounts_with_line_index.append((idx, val))

    total_amount: Optional[Decimal] = None
    if totals_found:
        total_amount = max(totals_found)
    elif amounts_with_line_index:
        total_amount = max(val for _, val in amounts_with_line_index)

    amounts_all: List[Decimal] = []
    if total_amount is not None:
        total_line_indexes = {li for li, v in amounts_with_line_index if v == total_amount}
        for li, v in amounts_with_line_index:
            if li in total_line_indexes:
                continue
            if (v * 100) % 1 == 0:
                amounts_all.append(v)
    else:
        for _, v in amounts_with_line_index:
            if (v * 100) % 1 == 0:
                amounts_all.append(v)

    return amounts_all, amounts_with_line_index, total_amount

def sum_and_compare(items: List[Decimal], total: Optional[Decimal], tolerance: Decimal = Decimal("0.02")) -> Tuple[Decimal, bool]:
    sum_items = sum(items, start=Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if total is None:
        return sum_items, False
    return sum_items, (abs(sum_items - total) <= tolerance)

def main() -> None:
    configure_tesseract()
    image_path = os.path.join(os.getcwd(), "factura.jpg")
    try:
        img = load_image(image_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print("Leyendo texto con OCR...")
    text = ocr_extract_text(img)
    print("\n=== TEXTO OCR EXTRAÍDO ===\n")
    print(text)

    items, _items_with_idx, total = extract_amounts_from_text(text)

    print("\n=== DETECCIÓN DE MONTOS ===")
    if total is not None:
        print(f"Total detectado: {total}")
    else:
        print("Total no detectado explícitamente; se usó heurística (máximo monto del documento si aplica).")

    if items:
        print("Ítems detectados (excluyendo la(s) línea(s) de total):")
        for v in items:
            print(f" - {v}")
    else:
        print("No se detectaron ítems con formato monetario claro (xx,dd o xx.dd).")

    sum_items, matches = sum_and_compare(items, total)
    print(f"\nSuma de ítems: {sum_items}")
    if total is not None:
        print(f"Total indicado: {total}")
        print("\nResultado:")
        if matches:
            print("✔ La suma de los ítems COINCIDE con el total (dentro de la tolerancia).")
        else:
            print("✘ La suma de los ítems NO coincide con el total.")
    else:
        print("No se pudo verificar la suma porque no se detectó un total.")

if __name__ == "__main__":
    main()
