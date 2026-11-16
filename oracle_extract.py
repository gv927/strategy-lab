#!/usr/bin/env python3
"""ORACLE PDF Extraction Engine - Cycle 1"""
import fitz
import os
import json
import sys

BOOKS_DIR = "/home/ubuntu/Desktop/data-download/BOOKS/"

def extract_pdf(filepath, max_pages=None):
    """Extract text from PDF, return dict with metadata and text per page."""
    try:
        doc = fitz.open(filepath)
        result = {
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "page_count": len(doc),
            "pages": {}
        }
        pages_to_read = range(len(doc)) if max_pages is None else range(min(max_pages, len(doc)))
        for i in pages_to_read:
            page = doc[i]
            text = page.get_text()
            if text.strip():
                result["pages"][i] = text
        doc.close()
        return result
    except Exception as e:
        return {"filename": os.path.basename(filepath), "error": str(e)}

def get_toc(filepath):
    """Get table of contents from PDF."""
    try:
        doc = fitz.open(filepath)
        toc = doc.get_toc()
        doc.close()
        return toc
    except:
        return []

# Priority files in order
priority_files = [
    # Wyckoff
    "0-Wyckoff_Spring.pdf",
    "10-Traditional_Wyckoff_schematic.pdf",
    "fulcrume wyckoff.pdf",
    "WYCKOFFxAMT.pdf",
    "What_and_who_is_wyckoff.pdf",
    "wyckoff-20-structures-volume-profile-and-order-flow-trading-and-investing-course-advanced-technical-analysis-book-2_compress.pdf",
    # ICT/SMC
    "PDF 01.pdf",
    "PDF 02.pdf",
    "PDF 03.pdf",
    "PDF 04.pdf",
    "Market Maker Traps (1).pdf",
    "Market Maker Traps (2).pdf",
    "Market Maker Traps (3).pdf",
    "Market Maker Traps (4).pdf",
    "smart-money-concepts-9-that-every-trader-must-know_compress.pdf",
    "market-structure-made-easy_compress.pdf",
    "market-structure-mastery-2_compress.pdf",
    "msnr-x-smc-x-ict-the-alchemist-yanu-emmanueL.pdf",
    # ICT ADV series
    "1- ADV_Spring_entry_SMT.pdf",
    "2-ADV_TEST_MODEL.pdf",
    "3-ADV_WYCKOFF_FRACTILITY_MTFHTF_DELIVERY.pdf",
    "4-ADV_MARKET_CORRELATION_SMT.pdf",
    "5-ADV_POINTS_OF_CONTROL.pdf",
    "6-ADV_Splitting_up_and_simplifying_the_schematic.pdf",
    "7-HTF_SESSION_LIQUIDITY_MODELS.pdf",
    "8-PD_ARRAY.pdf",
    "9-SC-BC.pdf",
    # Ichimoku
    "Cloud_Charts_Trading_Success_with_Ichimoku_Techniques.pdf",
    "Cloud_Charts_Trading_Success_with_the_Ichimoku_Technique_@Moneiac.pdf",
    "FxIchimoku_Grzegorz_MOskwa_EN.pdf",
    "Ichimoku Basic Master Book_Unlocked.pdf",
    "Ichimoku Charts - Nicole Elliott.pdf",
    "Kei_Ichimoku Advanced.pdf",
    "PeloilleTrading_with_Ichimoku_A_practical_guide_to_low_risk_Ichimoku.pdf",
    "Khalid El Bouzidi -Trader L Ichimoku - LIVRE Tome1.pdf",
    # Price Action
    "Trading Price Action Ranges_Trading Range - Al Brooks.pdf",
    "Understanding Price Action @Moneiac_Book.pdf",
    "[Bill_Eykyn]_Price_Action_Trading.pdf",
    "Forex Price Action Scalping Vol1 @Moneiac Book.pdf",
    "Forex Price Action Scalping Vol2 @Moneiac Book.pdf",
    "Price Action Market Traps 7 Trap.pdf",
    # Fibonacci
    "Fibonacci_Trading_-_How_to_Master_the_Time_and_Price_Advantage_by_Carolyn_Boroden.pdf",
    "Fibonacci for the Active Trader @Moneiac Book.pdf",
    # Additional
    "MMXM.pdf",
    "advance-liquidity-trading-concept-49_compress.pdf",
    "malaysian-snr-full.pdf",
    "SETTING_UP_THE_INDICATOR.pdf",
    "Technical_Analysis_of_the_Financial_Markets_A_Comprehensive_Guide.pdf",
    "Way-of-the-Turtle.pdf",
    "2008_Trend_Trading_for_a_Living_Learn_the_Skills_and_Gain_the_Confidence.pdf",
    "SIMPLE TRADING Book horus academy (1).pdf",
    "Simple+Trading+Book Horus Academy 2.pdf",
    "SMART MONEY CONCEPT ADAMAS 0.1 (1).pdf",
    "Zuessy - TIME.pdf",
    "info-forex-strategy.pdf",
    "trading-strategies-complex.pdf",
    "@StockPustak_The_1_Hour_Trade__Make_Money_With.pdf",
    "Forex_Made_Simple_A_Beginner_s_Guide.pdf",
]

all_extractions = {}
for fname in priority_files:
    fpath = os.path.join(BOOKS_DIR, fname)
    if not os.path.exists(fpath):
        print(f"MISSING: {fname}")
        continue
    
    # Check file size
    fsize = os.path.getsize(fpath)
    if fsize < 1024:
        print(f"SKIP (too small): {fname} ({fsize} bytes)")
        continue
    
    print(f"Extracting: {fname} ({fsize//1024}KB)")
    
    # Get TOC
    toc = get_toc(fpath)
    
    # Extract all text (no page limit for comprehensive extraction)
    result = extract_pdf(fpath)
    result["toc"] = toc
    result["file_size_kb"] = fsize // 1024
    
    total_chars = sum(len(t) for t in result.get("pages", {}).values())
    print(f"  -> {result['page_count']} pages, {total_chars} chars extracted, {len(toc)} TOC entries")
    
    all_extractions[fname] = result

# Save extracted text to JSON for processing
output_path = "/home/ubuntu/oracle_raw_extractions.json"
with open(output_path, "w") as f:
    json.dump(all_extractions, f, ensure_ascii=False)
print(f"\nSaved extractions to {output_path}")
print(f"Total books processed: {len(all_extractions)}")
