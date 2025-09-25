"""
Streamlit Web Application for OCR and Financial Document Verification
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import time
import os
from typing import Dict, Any

from ocr_engine import OCRApp, OCREngine, OCRResult, VerificationResult, GOOGLE_VISION_AVAILABLE

# Page configuration
st.set_page_config(
    page_title="OCR Financial Verifier",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .error-card {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
</style>
""", unsafe_allow_html=True)

def initialize_app():
    """Initialize the OCR application"""
    if 'ocr_app' not in st.session_state:
        # Check for Tesseract path
        tesseract_path = st.sidebar.text_input(
            "Tesseract Path (Windows)",
            value=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            help="Path to tesseract.exe on Windows"
        )
        
        # Check for Google Cloud credentials
        google_creds = st.sidebar.text_input(
            "Google Cloud Credentials Path",
            value="",
            help="Path to Google Cloud service account JSON file"
        )
        
        if google_creds and not os.path.exists(google_creds):
            st.sidebar.warning("Google Cloud credentials file not found")
            google_creds = None
        
        st.session_state.ocr_app = OCRApp(tesseract_path, google_creds)

def display_ocr_results(ocr_result: OCRResult):
    """Display OCR extraction results"""
    st.subheader("📝 Texto Extraído")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Motor OCR", ocr_result.engine.value.title())
    with col2:
        st.metric("Confianza", f"{ocr_result.confidence:.1%}")
    with col3:
        st.metric("Tiempo", f"{ocr_result.processing_time:.2f}s")
    
    # Display extracted text
    st.text_area("Texto completo:", ocr_result.text, height=200)

def display_verification_results(verification: VerificationResult):
    """Display calculation verification results"""
    st.subheader("🧮 Verificación de Cálculos")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ítems Encontrados", len(verification.items))
    
    with col2:
        if verification.total:
            st.metric("Total Detectado", f"${verification.total.value:.2f}")
        else:
            st.metric("Total Detectado", "No encontrado")
    
    with col3:
        st.metric("Suma Calculada", f"${verification.calculated_sum:.2f}")
    
    with col4:
        if verification.total:
            diff = verification.difference
            st.metric("Diferencia", f"${diff:.2f}")
        else:
            st.metric("Diferencia", "N/A")
    
    # Verification result
    if verification.total:
        if verification.matches:
            st.success("✅ **La suma de los ítems COINCIDE con el total** (dentro de la tolerancia)")
        else:
            st.error("❌ **La suma de los ítems NO coincide con el total**")
    else:
        st.warning("⚠️ **No se pudo detectar un total para verificar**")
    
    # Detailed breakdown
    if verification.items:
        st.subheader("📊 Desglose de Ítems")
        
        # Create DataFrame for items
        items_data = []
        for i, item in enumerate(verification.items, 1):
            items_data.append({
                'Ítem': i,
                'Valor': f"${item.value:.2f}",
                'Línea': item.line_number + 1,
                'Contexto': item.context[:50] + "..." if len(item.context) > 50 else item.context
            })
        
        df_items = pd.DataFrame(items_data)
        st.dataframe(df_items, use_container_width=True)
        
        # Visualization
        fig = px.bar(
            x=[f"Ítem {i+1}" for i in range(len(verification.items))],
            y=[item.value for item in verification.items],
            title="Valores de Ítems Detectados",
            labels={'x': 'Ítems', 'y': 'Valor ($)'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Total information
    if verification.total:
        st.subheader("💰 Información del Total")
        st.info(f"""
        **Valor del Total:** ${verification.total.value:.2f}  
        **Línea:** {verification.total.line_number + 1}  
        **Contexto:** {verification.total.context}
        """)

def display_engine_comparison(comparison_results: Dict[str, Any]):
    """Display comparison between OCR engines"""
    st.subheader("⚖️ Comparación de Motores OCR")
    
    engines = ['tesseract', 'google_vision']
    engine_names = ['Tesseract', 'Google Cloud Vision']
    
    # Create comparison metrics
    comparison_data = []
    
    for engine, name in zip(engines, engine_names):
        if engine in comparison_results and comparison_results[engine]['success']:
            result = comparison_results[engine]
            ocr_result = result['ocr_result']
            verification = result['verification']
            
            comparison_data.append({
                'Motor': name,
                'Confianza': f"{ocr_result.confidence:.1%}",
                'Tiempo (s)': f"{ocr_result.processing_time:.2f}",
                'Caracteres': len(ocr_result.text),
                'Ítems': len(verification.items) if verification else 0,
                'Total Detectado': "Sí" if verification and verification.total else "No",
                'Verificación': "✅" if verification and verification.matches else "❌"
            })
        else:
            error_msg = comparison_results[engine].get('error', 'Error desconocido')
            comparison_data.append({
                'Motor': name,
                'Confianza': "N/A",
                'Tiempo (s)': "N/A",
                'Caracteres': "N/A",
                'Ítems': "N/A",
                'Total Detectado': "N/A",
                'Verificación': f"❌ {error_msg}"
            })
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True)
    
    # Side-by-side text comparison
    if all(engine in comparison_results and comparison_results[engine]['success'] for engine in engines):
        st.subheader("📝 Comparación de Texto Extraído")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Tesseract:**")
            tesseract_text = comparison_results['tesseract']['ocr_result'].text
            st.text_area("", tesseract_text, height=200, key="tesseract_text")
        
        with col2:
            st.write("**Google Cloud Vision:**")
            google_text = comparison_results['google_vision']['ocr_result'].text
            st.text_area("", google_text, height=200, key="google_text")

def main():
    """Main application function"""
    # Header
    st.markdown('<h1 class="main-header">📄 OCR Financial Verifier</h1>', unsafe_allow_html=True)
    st.markdown("""
    Una aplicación avanzada para extraer información de documentos financieros usando OCR 
    y verificar la exactitud de los cálculos. Soporta tanto Tesseract como Google Cloud Vision.
    """)
    
    # Initialize app
    initialize_app()
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuración")
    
    # OCR Engine selection
    available_engines = ["Tesseract"]
    if GOOGLE_VISION_AVAILABLE:
        available_engines.append("Google Cloud Vision")
    
    selected_engine = st.sidebar.selectbox(
        "Motor OCR",
        available_engines,
        help="Selecciona el motor OCR a utilizar"
    )
    
    engine_map = {
        "Tesseract": OCREngine.TESSERACT,
        "Google Cloud Vision": OCREngine.GOOGLE_VISION
    }
    
    # File upload
    st.header("📤 Subir Imagen")
    
    uploaded_file = st.file_uploader(
        "Selecciona una imagen de factura o documento financiero",
        type=['png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        help="Formatos soportados: PNG, JPG, JPEG, TIFF, BMP"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(image, caption="Imagen subida", use_column_width=True)
            st.write(f"**Tamaño:** {image.size[0]} x {image.size[1]} píxeles")
            st.write(f"**Formato:** {image.format}")
        
        with col2:
            # Processing options
            st.subheader("🔧 Opciones de Procesamiento")
            
            compare_engines = st.checkbox(
                "Comparar ambos motores OCR",
                help="Procesa la imagen con ambos motores y compara resultados"
            )
            
            if st.button("🚀 Procesar Imagen", type="primary"):
                # Save uploaded file temporarily
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    if compare_engines and len(available_engines) > 1:
                        # Compare engines
                        with st.spinner("Comparando motores OCR..."):
                            comparison_results = st.session_state.ocr_app.compare_engines(temp_path)
                        
                        display_engine_comparison(comparison_results)
                        
                        # Show individual results
                        for engine_name in available_engines:
                            if engine_name.lower().replace(" ", "_") in comparison_results:
                                engine_key = engine_name.lower().replace(" ", "_")
                                result = comparison_results[engine_key]
                                
                                if result['success']:
                                    st.subheader(f"📊 Resultados - {engine_name}")
                                    display_ocr_results(result['ocr_result'])
                                    display_verification_results(result['verification'])
                                    st.divider()
                    
                    else:
                        # Single engine processing
                        with st.spinner(f"Procesando con {selected_engine}..."):
                            result = st.session_state.ocr_app.process_image(
                                temp_path, 
                                engine_map[selected_engine]
                            )
                        
                        if result['success']:
                            display_ocr_results(result['ocr_result'])
                            display_verification_results(result['verification'])
                        else:
                            st.error(f"Error al procesar la imagen: {result['error']}")
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    # Sample data section
    st.header("📚 Datos de Ejemplo")
    
    st.markdown("""
    ### Imágenes de Prueba Recomendadas
    
    Puedes descargar imágenes de prueba desde:
    - **Kaggle**: [Invoice OCR Dataset](https://www.kaggle.com/datasets)
    - **Google Images**: Busca "invoice sample" o "receipt sample"
    - **Documentos propios**: Facturas, recibos, estados de cuenta
    
    ### Formatos Soportados
    - **Imágenes**: PNG, JPG, JPEG, TIFF, BMP
    - **Idiomas**: Español, Inglés (configurable)
    - **Tipos de documento**: Facturas, recibos, estados de cuenta, tickets
    
    ### Consejos para Mejores Resultados
    1. **Calidad de imagen**: Usa imágenes nítidas y bien iluminadas
    2. **Resolución**: Mínimo 300 DPI recomendado
    3. **Formato**: PNG o TIFF para mejor calidad
    4. **Orientación**: Asegúrate de que el texto esté derecho
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>OCR Financial Verifier - Desarrollado con Streamlit, Tesseract y Google Cloud Vision</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
