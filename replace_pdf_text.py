"""
Generic PDF text replacement script using PyMuPDF.
Preserves original formatting and creates a new PDF file.

Dependencies:
    - PyMuPDF (install with: pip install PyMuPDF)
"""
import sys
import os
from pathlib import Path

# Check for required dependencies
try:
    import pymupdf
except ImportError:
    print("=" * 60)
    print("ERROR: Required dependency 'PyMuPDF' is not installed.")
    print("=" * 60)
    print("\nPlease install it using:")
    print("  pip install PyMuPDF")
    print("\nOr:")
    print("  python -m pip install PyMuPDF")
    print("=" * 60)
    print("\nPress Enter to exit...")
    try:
        input()
    except:
        pass
    sys.exit(1)


def replace_text_in_pdf(pdf_path, old_text, new_text, output_path=None):
    """
    Replace text in PDF. Simple 1:1 replacement.
    If original font not available, use default font for all text in entire PDF.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return False
    
    # Generate output filename if not provided
    if output_path is None:
        pdf_file = Path(pdf_path)
        output_path = str(pdf_file.parent / f"{pdf_file.stem}_updated{pdf_file.suffix}")
    
    print(f"\nOpening PDF: {pdf_path}")
    try:
        # Open the PDF
        doc = pymupdf.open(pdf_path)
        print(f"PDF opened successfully. Number of pages: {len(doc)}")
        
        default_font = "helv"
        original_font_available = True
        replacements_count = 0
        
        # First pass: Try replacements with original font
        print(f"\nAttempting replacements with original fonts...")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            if "blocks" not in blocks:
                continue
            
            for block in blocks["blocks"]:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    if "spans" not in line:
                        continue
                    
                    for span in line["spans"]:
                        span_text = span.get("text", "")
                        
                        if old_text.lower() in span_text.lower():
                            font = span.get("font", "")
                            size = span.get("size", 12)
                            color = span.get("color", 0)
                            bbox = span.get("bbox", [])
                            
                            if len(bbox) != 4:
                                continue
                            
                            rect = pymupdf.Rect(bbox)
                            
                            # Replace text
                            if old_text in span_text:
                                updated_text = span_text.replace(old_text, new_text)
                            else:
                                idx = span_text.lower().find(old_text.lower())
                                if idx >= 0:
                                    updated_text = span_text[:idx] + new_text + span_text[idx + len(old_text):]
                                else:
                                    updated_text = span_text.replace(old_text.lower(), new_text.lower())
                            
                            # Cover old text
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            
                            # Try with original font
                            if font:
                                try:
                                    page.insert_text(
                                        rect.tl,
                                        updated_text,
                                        fontsize=size,
                                        fontname=font,
                                        color=color if isinstance(color, (list, tuple)) else (0, 0, 0),
                                    )
                                    replacements_count += 1
                                except Exception:
                                    # Original font not available
                                    original_font_available = False
                                    print(f"  Page {page_num + 1}: Original font '{font}' not available")
        
        # If original font failed, redo only the affected blocks/paragraphs with default font
        if not original_font_available:
            print(f"\nOriginal font not available. Converting affected blocks to default font '{default_font}'...")
            
            # Reload document
            doc.close()
            doc = pymupdf.open(pdf_path)
            
            # Process pages - only change font in blocks that contain the replacement text
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                if "blocks" not in blocks:
                    continue
                
                # Process each block
                for block in blocks["blocks"]:
                    if "lines" not in block:
                        continue
                    
                    # Check if this block contains the text to replace
                    block_contains_target = False
                    block_spans = []
                    
                    for line in block["lines"]:
                        if "spans" not in line:
                            continue
                        for span in line["spans"]:
                            span_text = span.get("text", "")
                            if span_text.strip():
                                block_spans.append({
                                    "text": span_text,
                                    "bbox": span.get("bbox", []),
                                    "size": span.get("size", 12),
                                    "color": span.get("color", 0),
                                })
                                if old_text.lower() in span_text.lower():
                                    block_contains_target = True
                    
                    # Only process blocks that contain the target text
                    if block_contains_target:
                        # Cover all spans in this block with white rectangles
                        for span_info in block_spans:
                            if len(span_info["bbox"]) == 4:
                                rect = pymupdf.Rect(span_info["bbox"])
                                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                        
                        # Re-insert all text in this block with default font
                        for span_info in block_spans:
                            if len(span_info["bbox"]) != 4:
                                continue
                            
                            rect = pymupdf.Rect(span_info["bbox"])
                            text = span_info["text"]
                            size = span_info["size"]
                            color = span_info["color"]
                            
                            # Replace text if this is a replacement target
                            if old_text.lower() in text.lower():
                                if old_text in text:
                                    text = text.replace(old_text, new_text)
                                else:
                                    idx = text.lower().find(old_text.lower())
                                    if idx >= 0:
                                        text = text[:idx] + new_text + text[idx + len(old_text):]
                                    else:
                                        text = text.replace(old_text.lower(), new_text.lower())
                                replacements_count += 1
                            
                            # Insert with default font
                            try:
                                page.insert_text(
                                    rect.tl,
                                    text,
                                    fontsize=size,
                                    fontname=default_font,
                                    color=color if isinstance(color, (list, tuple)) else (0, 0, 0),
                                )
                            except Exception as e:
                                print(f"  Warning: Could not insert text on page {page_num + 1}: {e}")
        
        if replacements_count > 0:
            # Save to new file
            print(f"\nSaving to: {output_path}")
            doc.save(output_path)
            doc.close()
            print(f"Successfully replaced {replacements_count} instance(s) of '{old_text}' with '{new_text}'")
            if not original_font_available:
                print(f"Affected blocks converted to default font '{default_font}'")
            print(f"New file saved to: {output_path}")
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"File size: {file_size:,} bytes")
            return True
        else:
            print(f"\n'{old_text}' not found in PDF")
            doc.close()
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        if 'doc' in locals():
            doc.close()
        return False


def main():
    """Main function with user input."""
    print("PDF Text Replacement Tool (PyMuPDF)")
    print("=" * 50)
    
    # Get PDF file path
    pdf_path = input("\nEnter PDF file path: ").strip().strip('"').strip("'")
    
    if not pdf_path:
        print("Error: No file path provided")
        return
    
    # Get text to find
    old_text = input("Enter text to find: ").strip()
    if not old_text:
        print("Error: No search text provided")
        return
    
    # Get replacement text
    new_text = input("Enter replacement text: ").strip()
    if not new_text:
        print("Error: No replacement text provided")
        return
    
    # Generate output path
    pdf_file = Path(pdf_path)
    output_path = str(pdf_file.parent / f"{pdf_file.stem}_updated{pdf_file.suffix}")
    
    # Confirm
    print(f"\nWill replace '{old_text}' with '{new_text}' in:")
    print(f"  Input:  {pdf_path}")
    print(f"  Output: {output_path}")
    print("\nNote: If original font is not available, affected blocks will use default font.")
    confirm = input("\nContinue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Perform replacement
    print("\n" + "=" * 50)
    success = replace_text_in_pdf(pdf_path, old_text, new_text, output_path)
    print("=" * 50)
    
    if success:
        print("\nProcess completed successfully!")
    else:
        print("\nProcess failed or no replacements made.")
    
    # Keep console open
    print("\nPress Enter to exit...")
    try:
        input()
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nPress Enter to exit...")
        try:
            input()
        except:
            pass
