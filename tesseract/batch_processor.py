"""
Batch Processing Module for OCR Application
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

from ocr_engine import OCRApp, OCREngine, OCRResult, VerificationResult


class BatchProcessor:
    """Batch processing for multiple images"""
    
    def __init__(self, ocr_app: OCRApp, max_workers: int = 4):
        self.ocr_app = ocr_app
        self.max_workers = max_workers
        self.results = []
    
    def process_single_image(self, image_path: str, engine: OCREngine) -> Dict[str, Any]:
        """Process a single image and return results"""
        try:
            result = self.ocr_app.process_image(image_path, engine)
            result['image_path'] = image_path
            result['timestamp'] = datetime.now().isoformat()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'image_path': image_path,
                'timestamp': datetime.now().isoformat(),
                'ocr_result': None,
                'verification': None
            }
    
    def process_directory(self, directory_path: str, engine: OCREngine = OCREngine.TESSERACT, 
                         file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """Process all images in a directory"""
        if file_extensions is None:
            file_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all image files
        image_files = []
        for ext in file_extensions:
            image_files.extend(directory.glob(f"*{ext}"))
            image_files.extend(directory.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No image files found in {directory_path}")
            return []
        
        print(f"Found {len(image_files)} images to process")
        
        # Process images in parallel
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.process_single_image, str(img_path), engine): str(img_path)
                for img_path in image_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                img_path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Progress update
                    print(f"Processed: {os.path.basename(img_path)} - "
                          f"{'Success' if result['success'] else 'Failed'}")
                    
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'image_path': img_path,
                        'timestamp': datetime.now().isoformat()
                    })
        
        processing_time = time.time() - start_time
        print(f"Batch processing completed in {processing_time:.2f} seconds")
        
        self.results = results
        return results
    
    def save_results(self, output_path: str, format: str = 'json'):
        """Save batch processing results"""
        if not self.results:
            print("No results to save")
            return
        
        if format.lower() == 'json':
            self._save_json(output_path)
        elif format.lower() == 'csv':
            self._save_csv(output_path)
        elif format.lower() == 'excel':
            self._save_excel(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _save_json(self, output_path: str):
        """Save results as JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Results saved to {output_path}")
    
    def _save_csv(self, output_path: str):
        """Save results as CSV"""
        # Flatten results for CSV
        flattened_data = []
        
        for result in self.results:
            row = {
                'image_path': result.get('image_path', ''),
                'success': result.get('success', False),
                'error': result.get('error', ''),
                'timestamp': result.get('timestamp', ''),
            }
            
            if result.get('ocr_result'):
                ocr = result['ocr_result']
                row.update({
                    'engine': ocr.engine.value,
                    'confidence': ocr.confidence,
                    'processing_time': ocr.processing_time,
                    'text_length': len(ocr.text)
                })
            
            if result.get('verification'):
                ver = result['verification']
                row.update({
                    'items_count': len(ver.items),
                    'total_detected': ver.total.value if ver.total else None,
                    'calculated_sum': ver.calculated_sum,
                    'matches': ver.matches,
                    'difference': ver.difference
                })
            
            flattened_data.append(row)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Results saved to {output_path}")
    
    def _save_excel(self, output_path: str):
        """Save results as Excel with multiple sheets"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for result in self.results:
                summary_data.append({
                    'Image': os.path.basename(result.get('image_path', '')),
                    'Success': result.get('success', False),
                    'Error': result.get('error', ''),
                    'Engine': result.get('ocr_result', {}).get('engine', {}).get('value', '') if result.get('ocr_result') else '',
                    'Confidence': result.get('ocr_result', {}).get('confidence', 0) if result.get('ocr_result') else 0,
                    'Items Count': len(result.get('verification', {}).get('items', [])) if result.get('verification') else 0,
                    'Total Detected': result.get('verification', {}).get('total', {}).get('value', '') if result.get('verification') and result.get('verification', {}).get('total') else '',
                    'Matches': result.get('verification', {}).get('matches', False) if result.get('verification') else False
                })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed results sheet
            detailed_data = []
            for result in self.results:
                if result.get('success') and result.get('ocr_result'):
                    detailed_data.append({
                        'Image': os.path.basename(result.get('image_path', '')),
                        'Text': result.get('ocr_result', {}).get('text', ''),
                        'Processing Time': result.get('ocr_result', {}).get('processing_time', 0),
                        'Items': str([item.value for item in result.get('verification', {}).get('items', [])]) if result.get('verification') else '',
                        'Total': result.get('verification', {}).get('total', {}).get('value', '') if result.get('verification') and result.get('verification', {}).get('total') else '',
                        'Calculated Sum': result.get('verification', {}).get('calculated_sum', '') if result.get('verification') else '',
                        'Verification Result': result.get('verification', {}).get('matches', '') if result.get('verification') else ''
                    })
            
            if detailed_data:
                df_detailed = pd.DataFrame(detailed_data)
                df_detailed.to_excel(writer, sheet_name='Detailed Results', index=False)
        
        print(f"Results saved to {output_path}")
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics from batch processing"""
        if not self.results:
            return {}
        
        total_images = len(self.results)
        successful = sum(1 for r in self.results if r.get('success', False))
        failed = total_images - successful
        
        # OCR statistics
        ocr_results = [r for r in self.results if r.get('ocr_result')]
        avg_confidence = sum(r['ocr_result'].confidence for r in ocr_results) / len(ocr_results) if ocr_results else 0
        avg_processing_time = sum(r['ocr_result'].processing_time for r in ocr_results) / len(ocr_results) if ocr_results else 0
        
        # Verification statistics
        verifications = [r for r in self.results if r.get('verification')]
        total_verifications = len(verifications)
        successful_verifications = sum(1 for r in verifications if r['verification'].matches)
        
        return {
            'total_images': total_images,
            'successful_processing': successful,
            'failed_processing': failed,
            'success_rate': successful / total_images if total_images > 0 else 0,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_processing_time,
            'total_verifications': total_verifications,
            'successful_verifications': successful_verifications,
            'verification_success_rate': successful_verifications / total_verifications if total_verifications > 0 else 0
        }


def main():
    """Command line interface for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch OCR Processing')
    parser.add_argument('directory', help='Directory containing images to process')
    parser.add_argument('--engine', choices=['tesseract', 'google_vision'], default='tesseract',
                       help='OCR engine to use')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv', 'excel'], default='json',
                       help='Output format')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--tesseract-path', help='Path to Tesseract executable')
    parser.add_argument('--google-creds', help='Path to Google Cloud credentials')
    
    args = parser.parse_args()
    
    # Initialize OCR app
    ocr_app = OCRApp(args.tesseract_path, args.google_creds)
    
    # Initialize batch processor
    processor = BatchProcessor(ocr_app, args.workers)
    
    # Process directory
    engine = OCREngine.TESSERACT if args.engine == 'tesseract' else OCREngine.GOOGLE_VISION
    results = processor.process_directory(args.directory, engine)
    
    # Save results
    if args.output:
        processor.save_results(args.output, args.format)
    else:
        # Default output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = f"ocr_batch_results_{timestamp}.{args.format}"
        processor.save_results(default_output, args.format)
    
    # Print summary
    stats = processor.get_summary_statistics()
    print("\n=== BATCH PROCESSING SUMMARY ===")
    print(f"Total images: {stats.get('total_images', 0)}")
    print(f"Successful: {stats.get('successful_processing', 0)}")
    print(f"Failed: {stats.get('failed_processing', 0)}")
    print(f"Success rate: {stats.get('success_rate', 0):.1%}")
    print(f"Average confidence: {stats.get('average_confidence', 0):.1%}")
    print(f"Average processing time: {stats.get('average_processing_time', 0):.2f}s")
    print(f"Verification success rate: {stats.get('verification_success_rate', 0):.1%}")


if __name__ == "__main__":
    main()
