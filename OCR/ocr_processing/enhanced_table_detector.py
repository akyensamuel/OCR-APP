"""
Enhanced Table Detector with Multiple Strategies
Handles complex real-world documents including handwritten tables
"""
import cv2
import numpy as np
import pytesseract
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from ocr_processing.smart_preprocessor import SmartImagePreprocessor, ImageQualityMetrics

logger = logging.getLogger(__name__)


@dataclass
class DetectionStrategy:
    """Information about a detection strategy"""
    name: str
    confidence: float
    cells_found: int
    method: str


class EnhancedTableDetector:
    """
    Multi-strategy table detector for complex documents
    Tries multiple approaches and selects the best result
    """
    
    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.preprocessor = SmartImagePreprocessor()
        self.strategies = []
        
    def detect_with_multiple_strategies(self, image_path: str) -> Tuple[Optional[Any], DetectionStrategy]:
        """
        Try multiple detection strategies and return the best result
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (best_table_structure, strategy_info)
        """
        logger.info("=== Starting multi-strategy table detection ===")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Preprocess image
        preprocessed, metrics = self.preprocessor.preprocess_for_table_detection(image)
        
        results = []
        
        # Strategy 1: Morphology-based detection (good for clear borders)
        logger.info("\n--- Strategy 1: Morphology-based detection ---")
        try:
            result1 = self._detect_morphology(preprocessed)
            if result1:
                confidence1 = self._calculate_confidence(result1, metrics)
                results.append((result1, DetectionStrategy(
                    name="Morphology",
                    confidence=confidence1,
                    cells_found=len(result1.cells) if hasattr(result1, 'cells') else 0,
                    method="morphology"
                )))
                logger.info(f"[OK] Morphology: {len(result1.cells)} cells, confidence: {confidence1:.1f}%")
        except Exception as e:
            logger.warning(f"[FAILED] Morphology failed: {e}")
        
        # Strategy 2: Contour-based detection (good for varying borders)
        logger.info("\n--- Strategy 2: Contour-based detection ---")
        try:
            result2 = self._detect_contours(preprocessed)
            if result2:
                confidence2 = self._calculate_confidence(result2, metrics)
                results.append((result2, DetectionStrategy(
                    name="Contours",
                    confidence=confidence2,
                    cells_found=len(result2.cells) if hasattr(result2, 'cells') else 0,
                    method="contours"
                )))
                logger.info(f"[OK] Contours: {len(result2.cells)} cells, confidence: {confidence2:.1f}%")
        except Exception as e:
            logger.warning(f"[FAILED] Contours failed: {e}")
        
        # Strategy 3: Hough Lines (good for clean straight lines)
        logger.info("\n--- Strategy 3: Hough Lines detection ---")
        try:
            result3 = self._detect_hough_lines(preprocessed)
            if result3:
                confidence3 = self._calculate_confidence(result3, metrics)
                results.append((result3, DetectionStrategy(
                    name="Hough Lines",
                    confidence=confidence3,
                    cells_found=len(result3.cells) if hasattr(result3, 'cells') else 0,
                    method="hough"
                )))
                logger.info(f"[OK] Hough: {len(result3.cells)} cells, confidence: {confidence3:.1f}%")
        except Exception as e:
            logger.warning(f"[FAILED] Hough failed: {e}")
        
        # Strategy 4: Text-block clustering (good for borderless tables)
        logger.info("\n--- Strategy 4: Text-block clustering ---")
        try:
            result4 = self._detect_text_blocks(preprocessed)
            if result4:
                confidence4 = self._calculate_confidence(result4, metrics)
                results.append((result4, DetectionStrategy(
                    name="Text Blocks",
                    confidence=confidence4,
                    cells_found=len(result4.cells) if hasattr(result4, 'cells') else 0,
                    method="textblocks"
                )))
                logger.info(f"[OK] Text blocks: {len(result4.cells)} cells, confidence: {confidence4:.1f}%")
        except Exception as e:
            logger.warning(f"[FAILED] Text blocks failed: {e}")
        
        # Strategy 5: Hybrid approach (combination of methods)
        logger.info("\n--- Strategy 5: Hybrid detection ---")
        try:
            result5 = self._detect_hybrid(preprocessed, image)
            if result5:
                confidence5 = self._calculate_confidence(result5, metrics)
                results.append((result5, DetectionStrategy(
                    name="Hybrid",
                    confidence=confidence5,
                    cells_found=len(result5.cells) if hasattr(result5, 'cells') else 0,
                    method="hybrid"
                )))
                logger.info(f"[OK] Hybrid: {len(result5.cells)} cells, confidence: {confidence5:.1f}%")
        except Exception as e:
            logger.warning(f"[FAILED] Hybrid failed: {e}")
        
        # Select best result
        if not results:
            logger.error("[ERROR] All detection strategies failed")
            return None, DetectionStrategy("None", 0, 0, "none")
        
        # Sort by confidence
        results.sort(key=lambda x: x[1].confidence, reverse=True)
        best_result, best_strategy = results[0]
        
        logger.info(f"\n[WINNER] Best strategy: {best_strategy.name} "
                   f"(confidence: {best_strategy.confidence:.1f}%, "
                   f"cells: {best_strategy.cells_found})")
        
        # Store all strategies for analysis
        self.strategies = [strategy for _, strategy in results]
        
        return best_result, best_strategy
    
    def _detect_morphology(self, image: np.ndarray) -> Optional[Any]:
        """Detect table using morphological operations"""
        from ocr_processing.table_detector import TableDetector
        
        # Create temporary instance
        detector = TableDetector(self.ocr_engine)
        
        # Apply morphology-based detection
        binary = detector.preprocess_image(image)
        
        # Detect horizontal and vertical lines
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        
        h_lines_img = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel, iterations=2)
        v_lines_img = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel, iterations=2)
        
        # Find contours of lines
        h_contours, _ = cv2.findContours(h_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        v_contours, _ = cv2.findContours(v_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Extract line positions
        h_lines = []
        for contour in h_contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > image.shape[1] * 0.3:  # At least 30% of image width
                h_lines.append(y + h//2)
        
        v_lines = []
        for contour in v_contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > image.shape[0] * 0.3:  # At least 30% of image height
                v_lines.append(x + w//2)
        
        if len(h_lines) < 2 or len(v_lines) < 2:
            return None
        
        # Build grid and create table structure
        h_lines = sorted(set(h_lines))
        v_lines = sorted(set(v_lines))
        
        cells = detector.build_grid(h_lines, v_lines)
        
        from ocr_processing.table_detector import TableStructure
        return TableStructure(
            rows=len(h_lines) - 1,
            cols=len(v_lines) - 1,
            cells=cells,
            headers={},
            grid_confidence=0.8
        )
    
    def _detect_contours(self, image: np.ndarray) -> Optional[Any]:
        """Detect table using contour detection"""
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find all contours
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size (potential cells)
        min_area = 500  # Minimum cell area
        cell_contours = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter by aspect ratio (cells shouldn't be too elongated)
                aspect_ratio = w / h if h > 0 else 0
                if 0.1 < aspect_ratio < 10:
                    cell_contours.append((x, y, w, h))
        
        if len(cell_contours) < 5:  # Need at least 5 cells for a table
            return None
        
        # Organize contours into grid structure
        from ocr_processing.table_detector import CellInfo, TableStructure
        
        # Sort by y-coordinate (rows) and x-coordinate (columns)
        sorted_cells = sorted(cell_contours, key=lambda c: (c[1], c[0]))
        
        # Group into rows
        rows = []
        current_row = []
        current_y = sorted_cells[0][1]
        y_threshold = 20  # Pixels tolerance for same row
        
        for x, y, w, h in sorted_cells:
            if abs(y - current_y) < y_threshold:
                current_row.append((x, y, w, h))
            else:
                if current_row:
                    rows.append(sorted(current_row, key=lambda c: c[0]))
                current_row = [(x, y, w, h)]
                current_y = y
        
        if current_row:
            rows.append(sorted(current_row, key=lambda c: c[0]))
        
        # Create cells
        cells = []
        max_cols = max(len(row) for row in rows) if rows else 0
        
        for row_idx, row in enumerate(rows):
            for col_idx, (x, y, w, h) in enumerate(row):
                cells.append(CellInfo(
                    row=row_idx,
                    col=col_idx,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    is_header=(row_idx == 0)
                ))
        
        return TableStructure(
            rows=len(rows),
            cols=max_cols,
            cells=cells,
            headers={},
            grid_confidence=0.75
        )
    
    def _detect_hough_lines(self, image: np.ndarray) -> Optional[Any]:
        """Detect table using Hough Line Transform"""
        from ocr_processing.table_detector import TableDetector, TableStructure
        
        detector = TableDetector(self.ocr_engine)
        
        # Use the detector's built-in Hough method
        try:
            h_lines, v_lines = detector.detect_grid_with_hough(image)
            
            if len(h_lines) < 2 or len(v_lines) < 2:
                return None
            
            cells = detector.build_grid(h_lines, v_lines)
            
            return TableStructure(
                rows=len(h_lines) - 1,
                cols=len(v_lines) - 1,
                cells=cells,
                headers={},
                grid_confidence=0.7
            )
        except Exception as e:
            logger.warning(f"Hough line detection failed: {e}")
            return None
    
    def _detect_text_blocks(self, image: np.ndarray) -> Optional[Any]:
        """Detect table by clustering text blocks (for borderless tables)"""
        try:
            # Use pytesseract to get text blocks
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract blocks with confidence > 50
            blocks = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 50:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    text = data['text'][i].strip()
                    
                    if text:
                        blocks.append((x, y, w, h, text))
            
            if len(blocks) < 5:
                return None
            
            # Cluster blocks into rows and columns
            from ocr_processing.table_detector import CellInfo, TableStructure
            
            # Sort by y-coordinate
            blocks.sort(key=lambda b: b[1])
            
            # Group into rows
            rows = []
            current_row = []
            current_y = blocks[0][1]
            y_threshold = 30
            
            for x, y, w, h, text in blocks:
                if abs(y - current_y) < y_threshold:
                    current_row.append((x, y, w, h, text))
                else:
                    if current_row:
                        rows.append(sorted(current_row, key=lambda b: b[0]))
                    current_row = [(x, y, w, h, text)]
                    current_y = y
            
            if current_row:
                rows.append(sorted(current_row, key=lambda b: b[0]))
            
            # Create cells
            cells = []
            max_cols = max(len(row) for row in rows) if rows else 0
            
            for row_idx, row in enumerate(rows):
                for col_idx, (x, y, w, h, text) in enumerate(row):
                    cells.append(CellInfo(
                        row=row_idx,
                        col=col_idx,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        text=text,
                        is_header=(row_idx == 0)
                    ))
            
            return TableStructure(
                rows=len(rows),
                cols=max_cols,
                cells=cells,
                headers={},
                grid_confidence=0.65
            )
            
        except Exception as e:
            logger.warning(f"Text block detection failed: {e}")
            return None
    
    def _detect_hybrid(self, preprocessed: np.ndarray, original: np.ndarray) -> Optional[Any]:
        """
        Hybrid approach: Combine multiple methods
        Use line detection for structure, contours for refinement, and text blocks for content
        """
        # Step 1: Get grid structure from lines
        structure_result = self._detect_morphology(preprocessed)
        if not structure_result:
            structure_result = self._detect_hough_lines(preprocessed)
        
        if not structure_result:
            # Fall back to contours only
            return self._detect_contours(preprocessed)
        
        # Step 2: Get text content from text blocks
        text_result = self._detect_text_blocks(preprocessed)
        
        if not text_result:
            return structure_result
        
        # Step 3: Merge results - use structure from lines, content from text blocks
        # Match text blocks to grid cells
        for cell in structure_result.cells:
            # Find text blocks that overlap with this cell
            cell_center_x = cell.x + cell.width // 2
            cell_center_y = cell.y + cell.height // 2
            
            for text_cell in text_result.cells:
                text_x = text_cell.x + text_cell.width // 2
                text_y = text_cell.y + text_cell.height // 2
                
                # Check if text block is inside grid cell
                if (cell.x <= text_x <= cell.x + cell.width and
                    cell.y <= text_y <= cell.y + cell.height):
                    cell.text = text_cell.text
                    break
        
        structure_result.grid_confidence = 0.85  # Hybrid has higher confidence
        return structure_result
    
    def _calculate_confidence(self, result: Any, metrics: ImageQualityMetrics) -> float:
        """
        Calculate confidence score for a detection result
        
        Args:
            result: TableStructure or similar
            metrics: Image quality metrics
            
        Returns:
            Confidence score (0-100)
        """
        if not result or not hasattr(result, 'cells'):
            return 0.0
        
        # Base confidence from result
        base_conf = result.grid_confidence * 100 if hasattr(result, 'grid_confidence') else 50
        
        # Adjust based on number of cells (expect 20-200 cells for typical table)
        cell_count = len(result.cells)
        if 20 <= cell_count <= 200:
            cell_score = 100
        elif cell_count < 5:
            cell_score = 30
        elif cell_count < 20:
            cell_score = 70
        else:
            cell_score = 80
        
        # Adjust based on image quality
        quality_score = metrics.quality_score
        
        # Weighted average
        confidence = (
            base_conf * 0.4 +
            cell_score * 0.3 +
            quality_score * 0.3
        )
        
        return min(100, confidence)
