# OCR Financial Verifier - Guía de Instalación y Configuración

## 🚀 Instalación Rápida

### 1. Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

### 2. Instalar Tesseract OCR

#### Windows:
1. Descargar Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar en la ruta por defecto: `C:\Program Files\Tesseract-OCR\`
3. Agregar al PATH del sistema (opcional)

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-spa
```

#### macOS:
```bash
brew install tesseract tesseract-lang
```

### 3. Configurar Google Cloud Vision (Opcional)

1. Crear proyecto en Google Cloud Console
2. Habilitar Vision API
3. Crear credenciales de servicio (JSON)
4. Descargar el archivo de credenciales
5. Configurar variable de entorno:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

## 🖥️ Ejecutar la Aplicación

### Interfaz Web (Streamlit)
```bash
streamlit run streamlit_app.py
```
La aplicación estará disponible en: http://localhost:8501

### Script de Línea de Comandos
```bash
python invoice_ocr_check.py
```

### Procesamiento por Lotes
```bash
python batch_processor.py /path/to/images --engine tesseract --output results.json
```

## 📁 Estructura del Proyecto

```
tesseract/
├── invoice_ocr_check.py      # Script original mejorado
├── ocr_engine.py            # Motor OCR con múltiples engines
├── streamlit_app.py         # Interfaz web
├── batch_processor.py       # Procesamiento por lotes
├── requirements.txt         # Dependencias
├── setup_guide.md          # Esta guía
└── factura.jpg             # Imagen de prueba
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# Tesseract path (Windows)
TESSERACT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"

# Google Cloud credentials
GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

### Personalización de Idiomas
Modificar en `ocr_engine.py`:
```python
# Cambiar idiomas soportados
text = pytesseract.image_to_string(image, lang="spa+eng+fra", config=config)
```

## 📊 Características Principales

### ✅ Motores OCR Soportados
- **Tesseract**: Open source, gratuito, configurable
- **Google Cloud Vision**: Mayor precisión, requiere API key

### ✅ Funcionalidades
- Extracción de texto con OCR
- Detección automática de montos monetarios
- Verificación de cálculos (suma de ítems vs total)
- Interfaz web intuitiva
- Procesamiento por lotes
- Comparación entre motores OCR
- Exportación de resultados (JSON, CSV, Excel)

### ✅ Formatos Soportados
- **Imágenes**: PNG, JPG, JPEG, TIFF, BMP
- **Idiomas**: Español, Inglés (extensible)
- **Documentos**: Facturas, recibos, estados de cuenta

## 🎯 Casos de Uso

### 1. Verificación de Facturas
- Subir imagen de factura
- Extraer texto automáticamente
- Verificar si la suma de ítems coincide con el total

### 2. Procesamiento por Lotes
- Procesar múltiples documentos
- Generar reportes de verificación
- Análisis estadístico de precisión

### 3. Comparación de Motores
- Evaluar precisión entre Tesseract y Google Vision
- Optimizar configuración según tipo de documento

## 🔍 Solución de Problemas

### Error: "Tesseract not found"
```bash
# Verificar instalación
tesseract --version

# Configurar ruta manualmente
export TESSERACT_PATH="/usr/bin/tesseract"  # Linux
# o en Windows: C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Error: "Google Cloud Vision not available"
```bash
# Instalar dependencia
pip install google-cloud-vision

# Configurar credenciales
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

### Baja precisión en OCR
1. Mejorar calidad de imagen (resolución, contraste)
2. Usar Google Cloud Vision para mayor precisión
3. Ajustar parámetros de Tesseract (PSM mode)
4. Preprocesar imagen (escalado, filtros)

## 📈 Optimización de Rendimiento

### Para Procesamiento por Lotes
```python
# Ajustar número de workers
processor = BatchProcessor(ocr_app, max_workers=8)
```

### Para Mejor Precisión
```python
# Usar Google Cloud Vision
result = ocr_app.process_image(image_path, OCREngine.GOOGLE_VISION)
```

## 🧪 Datos de Prueba

### Fuentes Recomendadas
- **Kaggle**: [Invoice OCR Dataset](https://www.kaggle.com/datasets)
- **Google Images**: "invoice sample", "receipt sample"
- **Documentos propios**: Facturas, recibos reales

### Crear Imágenes de Prueba
```python
from PIL import Image, ImageDraw, ImageFont

# Crear factura de prueba
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)
# Agregar texto de factura...
img.save('test_invoice.png')
```

## 📞 Soporte

Para problemas o mejoras:
1. Revisar logs de error
2. Verificar configuración de dependencias
3. Probar con imágenes de alta calidad
4. Consultar documentación de Tesseract/Google Vision

## 🔄 Actualizaciones Futuras

- [ ] Soporte para más idiomas
- [ ] Integración con más motores OCR
- [ ] API REST para integración
- [ ] Machine Learning para mejor detección
- [ ] Interfaz móvil
- [ ] Integración con bases de datos
