# 📄 OCR Financial Verifier

Una aplicación avanzada para extraer información de documentos financieros usando OCR y verificar la exactitud de los cálculos. Soporta tanto Tesseract como Google Cloud Vision para máxima precisión.

## 🚀 Características Principales

- ✅ **Doble Motor OCR**: Tesseract (gratuito) + Google Cloud Vision (mayor precisión)
- ✅ **Verificación Automática**: Detecta si la suma de ítems coincide con el total
- ✅ **Interfaz Web Intuitiva**: Sube imágenes y ve resultados instantáneos
- ✅ **Procesamiento por Lotes**: Procesa múltiples documentos a la vez
- ✅ **Múltiples Formatos**: PNG, JPG, JPEG, TIFF, BMP
- ✅ **Exportación de Resultados**: JSON, CSV, Excel
- ✅ **Comparación de Motores**: Evalúa precisión entre diferentes OCR

## 📋 Requisitos Previos

### 1. Python 3.8+
```bash
python --version
```

### 2. Tesseract OCR

#### Windows:
1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar en: `C:\Program Files\Tesseract-OCR\`
3. (Opcional) Agregar al PATH del sistema

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-spa
```

#### macOS:
```bash
brew install tesseract tesseract-lang
```

### 3. Google Cloud Vision (Opcional - para mayor precisión)
1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Vision API
3. Crear credenciales de servicio (JSON)
4. Descargar archivo de credenciales

## 🛠️ Instalación

### Paso 1: Clonar/Descargar el Proyecto
```bash
# Si tienes git
git clone <repository-url>
cd tesseract

# O descargar y extraer el ZIP
```

### Paso 2: Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno (Opcional)
```bash
# Windows (PowerShell)
$env:TESSERACT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\credentials.json"

# Linux/macOS
export TESSERACT_PATH="/usr/bin/tesseract"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

## 🎯 Cómo Usar

### Opción 1: Interfaz Web (Recomendado)

#### Ejecutar la Aplicación:
```bash
streamlit run streamlit_app.py
```

#### En Windows (más fácil):
```bash
# Doble clic en:
run_app.bat
```

#### Acceder a la Aplicación:
- Abre tu navegador en: http://localhost:8501
- Sube una imagen de factura o documento financiero
- Selecciona el motor OCR (Tesseract o Google Vision)
- Haz clic en "Procesar Imagen"
- Ve los resultados de extracción y verificación

### Opción 2: Script de Línea de Comandos

#### Procesar una Imagen:
```bash
# Coloca tu imagen como "factura.jpg" en la carpeta del proyecto
python invoice_ocr_check.py
```

#### Procesar Imagen Específica:
```bash
# Modifica el script para cambiar la ruta de la imagen
# Línea 197: image_path = os.path.join(os.getcwd(), "tu_imagen.jpg")
```

### Opción 3: Procesamiento por Lotes

#### Procesar Carpeta Completa:
```bash
python batch_processor.py /ruta/a/tus/imagenes --engine tesseract --output resultados.json
```

#### Opciones Disponibles:
```bash
python batch_processor.py --help
```

## 📊 Ejemplos de Uso

### 1. Verificar una Factura
1. Toma una foto de una factura
2. Ejecuta `streamlit run streamlit_app.py`
3. Sube la imagen en la interfaz web
4. Ve si la suma de ítems coincide con el total

### 2. Procesar Múltiples Documentos
```bash
# Crear carpeta con imágenes
mkdir mis_facturas
# Copiar imágenes a la carpeta

# Procesar todas
python batch_processor.py mis_facturas --engine tesseract --format excel --output reporte.xlsx
```

### 3. Comparar Precisión de Motores
1. Ejecuta la interfaz web
2. Sube una imagen
3. Marca "Comparar ambos motores OCR"
4. Ve las diferencias entre Tesseract y Google Vision

## 📁 Estructura del Proyecto

```
tesseract/
├── invoice_ocr_check.py      # Script original mejorado
├── ocr_engine.py            # Motor OCR con múltiples engines
├── streamlit_app.py         # Interfaz web
├── batch_processor.py       # Procesamiento por lotes
├── requirements.txt         # Dependencias
├── setup_guide.md          # Guía detallada de configuración
├── README.md               # Este archivo
├── run_app.bat            # Script para Windows
└── factura.jpg            # Imagen de prueba (opcional)
```

## 🎨 Interfaz Web - Guía Visual

### Pantalla Principal:
1. **Subir Imagen**: Arrastra y suelta o haz clic para seleccionar
2. **Configuración**: Selecciona motor OCR en la barra lateral
3. **Procesar**: Haz clic en "Procesar Imagen"
4. **Resultados**: Ve texto extraído y verificación de cálculos

### Resultados Mostrados:
- ✅ **Texto Extraído**: Todo el texto detectado por OCR
- ✅ **Métricas**: Confianza, tiempo de procesamiento
- ✅ **Montos Detectados**: Lista de valores monetarios
- ✅ **Verificación**: Si la suma coincide con el total
- ✅ **Visualizaciones**: Gráficos de ítems y comparaciones

## 🔧 Configuración Avanzada

### Personalizar Tesseract:
```python
# En ocr_engine.py, línea 45
config = "--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,-$€£¥₡₱₲₵₴₹₽₺ "
```

### Agregar Más Idiomas:
```python
# En ocr_engine.py, línea 44
text = pytesseract.image_to_string(image, lang="spa+eng+fra", config=config)
```

### Ajustar Tolerancia de Verificación:
```python
# En ocr_engine.py, línea 200
def sum_and_compare(items, total, tolerance=Decimal("0.02")):  # Cambiar 0.02
```

## 📈 Consejos para Mejores Resultados

### Calidad de Imagen:
- ✅ **Resolución**: Mínimo 300 DPI
- ✅ **Iluminación**: Buena iluminación, sin sombras
- ✅ **Enfoque**: Texto nítido y legible
- ✅ **Orientación**: Documento derecho, no inclinado
- ✅ **Formato**: PNG o TIFF para mejor calidad

### Tipos de Documentos:
- ✅ **Facturas**: Funciona excelente
- ✅ **Recibos**: Muy bueno
- ✅ **Estados de Cuenta**: Bueno
- ✅ **Tickets**: Funciona bien
- ❌ **Manuscritos**: Limitado
- ❌ **Imágenes muy pequeñas**: Baja precisión

## 🐛 Solución de Problemas

### Error: "Tesseract not found"
```bash
# Verificar instalación
tesseract --version

# Configurar ruta manualmente en la interfaz web
# O en la barra lateral de Streamlit
```

### Error: "Google Cloud Vision not available"
```bash
# Instalar dependencia
pip install google-cloud-vision

# Configurar credenciales
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

### Baja Precisión en OCR:
1. **Mejorar imagen**: Mayor resolución, mejor contraste
2. **Usar Google Vision**: Mayor precisión que Tesseract
3. **Preprocesar imagen**: Escalar, ajustar contraste
4. **Ajustar parámetros**: Cambiar PSM mode en Tesseract

### La Aplicación No Inicia:
```bash
# Verificar dependencias
pip install -r requirements.txt

# Verificar Python
python --version  # Debe ser 3.8+

# Verificar Streamlit
streamlit --version
```

## 📊 Datos de Prueba

### Fuentes Recomendadas:
- **Kaggle**: [Invoice OCR Dataset](https://www.kaggle.com/datasets)
- **Google Images**: Busca "invoice sample", "receipt sample"
- **Documentos propios**: Facturas, recibos reales

### Crear Imagen de Prueba:
```python
from PIL import Image, ImageDraw, ImageFont

# Crear factura de prueba
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)
# Agregar texto de factura...
img.save('test_invoice.png')
```

## 🚀 Casos de Uso Avanzados

### 1. Integración con Sistemas:
```python
from ocr_engine import OCRApp

# Usar en tu código
app = OCRApp()
result = app.process_image("factura.jpg")
if result['success']:
    print(f"Total: {result['verification'].total.value}")
```

### 2. API REST (Futuro):
```python
# Ejemplo de uso como API
from flask import Flask, request, jsonify

app = Flask(__name__)
ocr_app = OCRApp()

@app.route('/process', methods=['POST'])
def process_image():
    # Procesar imagen subida
    result = ocr_app.process_image(request.files['image'])
    return jsonify(result)
```

### 3. Automatización:
```bash
# Script para procesar facturas diariamente
#!/bin/bash
python batch_processor.py /ruta/facturas/diarias --output reporte_$(date +%Y%m%d).xlsx
```

## 📞 Soporte y Contribuciones

### Para Reportar Problemas:
1. Verificar que todas las dependencias estén instaladas
2. Probar con imágenes de alta calidad
3. Revisar logs de error
4. Consultar documentación de Tesseract/Google Vision

### Para Mejoras:
- Agregar soporte para más idiomas
- Integrar más motores OCR
- Mejorar interfaz de usuario
- Optimizar rendimiento

## 📄 Licencia

Este proyecto está bajo licencia MIT. Puedes usarlo libremente para proyectos personales y comerciales.

## 🙏 Agradecimientos

- **Tesseract OCR**: Motor OCR open source
- **Google Cloud Vision**: API de reconocimiento de texto
- **Streamlit**: Framework para aplicaciones web
- **PIL/Pillow**: Procesamiento de imágenes
- **Kaggle**: Datasets de prueba

---

**¡Disfruta usando OCR Financial Verifier! 🎉**

Para más detalles técnicos, consulta `setup_guide.md`
