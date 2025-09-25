"""
OCR Engine Module - Supports both Tesseract and Google Cloud Vision
"""
import os
import re
import json
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    from PIL import Image
    import pytesseract
except ImportError as e:
    print(f"Error importing PIL/pytesseract: {e}")
    print("Install with: pip install pillow pytesseract")

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Google Cloud Vision not available. Install with: pip install google-cloud-vision")


class OCREngine(Enum):
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: OCREngine
    processing_time: float
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class AmountInfo:
    value: Decimal
    line_number: int
    context: str
    confidence: float = 1.0


@dataclass
class VerificationResult:
    items: List[AmountInfo]
    total: Optional[AmountInfo]
    calculated_sum: Decimal
    matches: bool
    difference: Decimal
    tolerance: Decimal = Decimal("0.02")


class OCREngineManager:
    def __init__(self, tesseract_path: str = None, google_credentials_path: str = None):
        self.tesseract_path = tesseract_path or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        self.google_credentials_path = google_credentials_path
        
        # Configure Tesseract
        if os.name == "nt" and os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Configure Google Vision
        if GOOGLE_VISION_AVAILABLE and self.google_credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.google_credentials_path

    def extract_text_tesseract(self, image: Image.Image, language: str = "spa+eng") -> OCRResult:
        """Extract text using Tesseract OCR"""
        import time
        start_time = time.time()
        
        try:
            # Try with Spanish + English
            config = "--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,-$€£¥₡₱₲₵₴₹₽₺ "
            text = pytesseract.image_to_string(image, lang=language, config=config)
            
            # Get confidence data
            data = pytesseract.image_to_data(image, lang=language, config=config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,
                engine=OCREngine.TESSERACT,
                processing_time=processing_time,
                raw_data=data
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                engine=OCREngine.TESSERACT,
                processing_time=processing_time
            )

    def extract_text_google_vision(self, image: Image.Image) -> OCRResult:
        """Extract text using Google Cloud Vision API"""
        if not GOOGLE_VISION_AVAILABLE:
            raise ImportError("Google Cloud Vision not available")
        
        import time
        start_time = time.time()
        
        try:
            client = vision.ImageAnnotatorClient()
            
            # Convert PIL image to bytes
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            vision_image = vision.Image(content=img_byte_arr)
            response = client.text_detection(image=vision_image)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            texts = response.text_annotations
            if texts:
                full_text = texts[0].description
                confidence = 1.0  # Google Vision doesn't provide confidence for full text
            else:
                full_text = ""
                confidence = 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text,
                confidence=confidence,
                engine=OCREngine.GOOGLE_VISION,
                processing_time=processing_time,
                raw_data={"annotations": [{"description": t.description, "bounding_poly": t.bounding_poly} for t in texts]}
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                engine=OCREngine.GOOGLE_VISION,
                processing_time=processing_time
            )

    def extract_text(self, image: Image.Image, engine: OCREngine = OCREngine.TESSERACT) -> OCRResult:
        """Extract text using specified OCR engine"""
        if engine == OCREngine.TESSERACT:
            return self.extract_text_tesseract(image)
        elif engine == OCREngine.GOOGLE_VISION:
            return self.extract_text_google_vision(image)
        else:
            raise ValueError(f"Unsupported OCR engine: {engine}")


class TextProcessor:
    """Advanced text processing for financial documents"""
    
    def __init__(self):
        # Enhanced regex patterns for different number formats
        self.money_patterns = [
            # Standard formats: 123.45, 1,234.56, 123,45
            r'(?:[\$€£¥₡₱₲₵₴₹₽₺]?\s*)?([+-]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})|[+-]?\d+[\.,]\d{2})',
            # Without currency symbol
            r'([+-]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})|[+-]?\d+[\.,]\d{2})',
            # Scientific notation
            r'([+-]?\d+\.?\d*[eE][+-]?\d+)',
        ]
        
        # Keywords for totals
        self.total_keywords = [
            r'\b(total|importe\s*total|total\s*a\s*pagar|gran\s*total|suma\s*total)\b',
            r'\b(subtotal|sub\s*total)\b',
            r'\b(iva|impuesto|tax)\b',
            r'\b(descuento|discount)\b',
            r'\b(propina|tip)\b'
        ]

    def normalize_amount(self, raw_amount: str) -> Optional[Decimal]:
        """Normalize various number formats to Decimal"""
        if not raw_amount:
            return None
            
        # Clean the string
        s = raw_amount.strip()
        s = re.sub(r'[\s\$€£¥₡₱₲₵₴₹₽₺]', '', s)
        
        if not s:
            return None

        try:
            # Handle different decimal separators
            comma_count = s.count(',')
            dot_count = s.count('.')
            
            if comma_count > 0 and dot_count > 0:
                # Both separators present - last one is decimal
                last_comma = s.rfind(',')
                last_dot = s.rfind('.')
                decimal_pos = max(last_comma, last_dot)
                
                if decimal_pos == last_dot:
                    # Dot is decimal separator
                    integer_part = s[:last_dot].replace(',', '')
                    decimal_part = s[last_dot+1:]
                else:
                    # Comma is decimal separator
                    integer_part = s[:last_comma].replace('.', '')
                    decimal_part = s[last_comma+1:]
                
                s_clean = integer_part + '.' + decimal_part
                
            elif comma_count > 0:
                # Only commas - check if it's decimal (ends with ,XX)
                if re.search(r',\d{2}$', s):
                    s_clean = s.replace(',', '.')
                else:
                    s_clean = s.replace(',', '')
                    
            elif dot_count > 0:
                # Only dots - check if it's decimal (ends with .XX)
                if re.search(r'\.\d{2}$', s):
                    s_clean = s
                else:
                    s_clean = s.replace('.', '')
            else:
                s_clean = s
            
            # Convert to Decimal and round to 2 decimal places
            value = Decimal(s_clean)
            return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (InvalidOperation, ValueError):
            return None

    def extract_amounts(self, text: str) -> List[AmountInfo]:
        """Extract all monetary amounts from text"""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        amounts = []
        
        for line_idx, line in enumerate(lines):
            for pattern in self.money_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    amount_str = match.group(1)
                    normalized = self.normalize_amount(amount_str)
                    
                    if normalized and normalized > 0:  # Only positive amounts
                        amounts.append(AmountInfo(
                            value=normalized,
                            line_number=line_idx,
                            context=line,
                            confidence=1.0
                        ))
        
        return amounts

    def identify_total(self, amounts: List[AmountInfo], text: str) -> Optional[AmountInfo]:
        """Identify the total amount from the list of amounts"""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # Look for amounts in lines with total keywords
        total_candidates = []
        
        for line_idx, line in enumerate(lines):
            for keyword_pattern in self.total_keywords:
                if re.search(keyword_pattern, line, re.IGNORECASE):
                    # Find amounts in this line
                    line_amounts = [amt for amt in amounts if amt.line_number == line_idx]
                    total_candidates.extend(line_amounts)
        
        if total_candidates:
            # Return the largest amount from total lines
            return max(total_candidates, key=lambda x: x.value)
        
        # Fallback: return the largest amount overall
        if amounts:
            return max(amounts, key=lambda x: x.value)
        
        return None

    def verify_calculations(self, text: str) -> VerificationResult:
        """Verify if the sum of items matches the total"""
        amounts = self.extract_amounts(text)
        total = self.identify_total(amounts, text)
        
        # Filter out the total from items
        items = []
        if total:
            items = [amt for amt in amounts if amt.value != total.value or amt.line_number != total.line_number]
        else:
            items = amounts
        
        # Calculate sum
        calculated_sum = sum(item.value for item in items)
        
        # Check if calculations match
        matches = False
        difference = Decimal('0')
        
        if total:
            difference = abs(calculated_sum - total.value)
            matches = difference <= Decimal('0.02')  # 2 cent tolerance
        
        return VerificationResult(
            items=items,
            total=total,
            calculated_sum=calculated_sum,
            matches=matches,
            difference=difference
        )


class OCRApp:
    """Main OCR Application Class"""
    
    def __init__(self, tesseract_path: str = None, google_credentials_path: str = None):
        self.engine_manager = OCREngineManager(tesseract_path, google_credentials_path)
        self.text_processor = TextProcessor()
    
    def process_image(self, image_path: str, engine: OCREngine = OCREngine.TESSERACT) -> Dict[str, Any]:
        """Process an image and return comprehensive results"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Extract text
            ocr_result = self.engine_manager.extract_text(image, engine)
            
            # Process text for financial verification
            verification = self.text_processor.verify_calculations(ocr_result.text)
            
            return {
                'success': True,
                'ocr_result': ocr_result,
                'verification': verification,
                'image_info': {
                    'size': image.size,
                    'mode': image.mode,
                    'format': image.format
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ocr_result': None,
                'verification': None
            }
    
    def compare_engines(self, image_path: str) -> Dict[str, Any]:
        """Compare results from both OCR engines"""
        results = {}
        
        # Test Tesseract
        try:
            results['tesseract'] = self.process_image(image_path, OCREngine.TESSERACT)
        except Exception as e:
            results['tesseract'] = {'success': False, 'error': str(e)}
        
        # Test Google Vision (if available)
        if GOOGLE_VISION_AVAILABLE:
            try:
                results['google_vision'] = self.process_image(image_path, OCREngine.GOOGLE_VISION)
            except Exception as e:
                results['google_vision'] = {'success': False, 'error': str(e)}
        else:
            results['google_vision'] = {'success': False, 'error': 'Google Cloud Vision not available'}
        
        return results
