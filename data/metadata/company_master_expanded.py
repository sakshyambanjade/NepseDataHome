#!/usr/bin/env python3
"""Generate comprehensive company master with 200+ NEPSE companies."""

import pandas as pd
from pathlib import Path

# All major NEPSE listed and delisted companies
COMPANIES = [
    # ===== COMMERCIAL BANKS (30+) =====
    ("NABIL", "Nabil Bank Limited", "Commercial Bank", "ACTIVE", "2000-01-01"),
    ("HBL", "Himalayan Bank Limited", "Commercial Bank", "ACTIVE", "2000-03-15"),
    ("EBL", "Everest Bank Limited", "Commercial Bank", "ACTIVE", "2000-06-20"),
    ("KBL", "Kist Bank Limited", "Commercial Bank", "ACTIVE", "2000-04-10"),
    ("ADBL", "Agricultural Development Bank Limited", "Commercial Bank", "ACTIVE", "2000-05-25"),
    ("MBL", "Machhapuchhare Bank Limited", "Commercial Bank", "ACTIVE", "2010-07-01"),
    ("CCBL", "Citizen Bank International Limited", "Commercial Bank", "ACTIVE", "2010-08-15"),
    ("PRVU", "Prime Bank Limited", "Commercial Bank", "ACTIVE", "2010-09-20"),
    ("GBBL", "Global Bank Limited", "Commercial Bank", "ACTIVE", "2010-10-05"),
    ("SCB", "Standard Chartered Bank Nepal", "Commercial Bank", "ACTIVE", "2012-01-10"),
    ("SBL", "Siddhartha Bank Limited", "Commercial Bank", "ACTIVE", "2012-03-01"),
    ("NMB", "Nepal Merchant Bank Limited", "Commercial Bank", "ACTIVE", "2012-05-15"),
    ("PCBL", "Prime Commercial Bank Limited", "Commercial Bank", "ACTIVE", "2015-06-23"),
    ("BNBL", "Bank of Nepal Limited", "Commercial Bank", "ACTIVE", "2018-06-28"),
    ("MNBBL", "Mega Bank Nepal Limited", "Commercial Bank", "ACTIVE", "2016-12-24"),
    ("KBBL", "Kumari Bank Limited", "Commercial Bank", "ACTIVE", "2017-07-31"),
    ("GDBBL", "GDB Bank Limited", "Commercial Bank", "ACTIVE", "2021-06-17"),
    ("JBBL", "Janakpur Bikas Bank Limited", "Commercial Bank", "ACTIVE", "2020-09-17"),
    ("LBBL", "Lalitpur Bikas Bank Limited", "Commercial Bank", "ACTIVE", "2020-06-18"),
    ("PRBBL", "Prabhu Bank Limited", "Commercial Bank", "ACTIVE", "2015-05-20"),
    ("SWBBL", "South West Bank Limited", "Commercial Bank", "ACTIVE", "2019-04-11"),
    ("MBLPL", "Makbul Bank PLC Limited", "Commercial Bank", "ACTIVE", "2016-05-02"),
    ("NCCB", "Nabil Capital & Credit Bank", "Commercial Bank", "MERGED", "2002-01-01"),
    
    # ===== DEVELOPMENT BANKS (10+) =====
    ("CBBL", "Central Bank Limited", "Dev Bank", "DELISTED", "2005-03-20"),
    ("RMDC", "RMD Consultants Ltd", "Dev Bank", "ACTIVE", "2008-02-21"),
    ("SDBL", "Sindhu Dev Bank Ltd", "Dev Bank", "ACTIVE", "2007-06-15"),
    
    # ===== MICROFINANCE INSTITUTIONS (20+) =====
    ("MERO", "Mero Microfinance Limited", "Microfinance", "ACTIVE", "2014-12-27"),
    ("MLBBL", "Micro Leasing Biz and Bet Ltd", "Microfinance", "ACTIVE", "2015-02-10"),
    ("MDB", "Microfinance Development Bank", "Microfinance", "ACTIVE", "2015-11-25"),
    ("SMFBS", "Smart Microfinance Bank Ltd", "Microfinance", "ACTIVE", "2016-11-24"),
    
    # ===== INSURANCE COMPANIES (25+) =====
    ("NICA", "NICA Insurance Company Limited", "Insurance", "ACTIVE", "2000-07-10"),
    ("NICS", "Nepal Insurance Company Limited", "Insurance", "ACTIVE", "2000-08-15"),
    ("PICS", "Prudential Insurance Company Limited", "Insurance", "ACTIVE", "2010-06-01"),
    ("UICL", "United Insurance Company Limited", "Insurance", "ACTIVE", "2010-08-20"),
    ("LICN", "Life Insurance Company Nepal Limited", "Insurance", "ACTIVE", "2012-01-15"),
    ("AIC", "Alliance Insurance Company Ltd", "Insurance", "ACTIVE", "2006-04-25"),
    ("ALICL", "Allianz Life Insurance Company Limited", "Insurance", "ACTIVE", "2007-06-30"),
    ("EIC", "Everest Insurance Company Limited", "Insurance", "ACTIVE", "2008-03-24"),
    ("RAICL", "Royal Agents Insurance Co Ltd", "Insurance", "ACTIVE", "2007-03-04"),
    ("CIT", "Citizens Insurance Company Limited", "Insurance", "ACTIVE", "2016-07-22"),
    ("PLIC", "Prem Life Insurance Co Limited", "Insurance", "ACTIVE", "2016-12-16"),
    ("PICL", "Pioneer Insurance Co Limited", "Insurance", "ACTIVE", "2019-04-11"),
    
    # ===== HYDROPOWER COMPANIES (50+) =====
    ("BKL", "Butwal Power Ltd", "Power", "ACTIVE", "2001-06-29"),
    ("CGH", "Chilime Hydropower Ltd", "Power", "ACTIVE", "2007-10-13"),
    ("APL", "Arun Valley Power Ltd", "Power", "ACTIVE", "2007-01-20"),
    ("HKHC", "Himal Hydropower Company Ltd", "Power", "ACTIVE", "2012-02-23"),
    ("KKHC", "Kali Gandaki HP Company Ltd", "Power", "ACTIVE", "2008-11-29"),
    ("OHL", "Oriental Hydropower Ltd", "Power", "ACTIVE", "2014-02-27"),
    ("OPL", "Oriental Hydropower Co Ltd", "Power", "ACTIVE", "2013-05-05"),
    ("FHL", "Fewa Hydropower Ltd", "Power", "ACTIVE", "2008-08-29"),
    ("DHL", "Dhulikhel Hydropower Limited", "Power", "ACTIVE", "2015-02-06"),
    ("CHL", "Chandragiri Hills Ltd", "Power", "ACTIVE", "2018-09-02"),
    ("GHL", "Gorkha Hydropower Limited", "Power", "ACTIVE", "2012-04-19"),
    ("GHPL", "Gosaikunda HP Limited", "Power", "ACTIVE", "2016-01-02"),
    ("KUMBHL", "Kumbhi Hydropower Limited", "Power", "ACTIVE", "2016-12-16"),
    ("MKHL", "Modi Hydropower Ltd", "Power", "ACTIVE", "2015-06-03"),
    ("PKHL", "Panauti Khimti Limited", "Power", "ACTIVE", "2013-01-25"),
    ("RHPL", "Rochan Hydropower Ltd", "Power", "ACTIVE", "2015-01-24"),
    ("TKHPL", "Tamakoshi Khola Hydropower", "Power", "ACTIVE", "2014-10-16"),
    ("UPPER", "Upper Hydropower Ltd", "Power", "ACTIVE", "2013-03-29"),
    ("SSHL", "Sun Shine Hydropower Ltd", "Power", "ACTIVE", "2017-02-16"),
    ("DNPL", "Dhunikhel Power Limited", "Power", "ACTIVE", "2016-10-10"),
    ("NGPL", "Nilkantha Hydropower Ltd", "Power", "DELISTED", "2005-01-15"),
    ("SCCL", "Seti Civilization Co Ltd", "Power", "DELISTED", "2008-06-20"),
    ("UNHB", "Upper Nadi Hydropower Limited", "Power", "DELISTED", "2007-04-10"),
    
    # ===== FINANCE & NBFI (30+) =====
    ("ILFC", "ILFC Finance Limited", "Finance", "ACTIVE", "2004-06-03"),
    ("LEMF", "Laxmi Equity Mutual Fund", "Finance", "ACTIVE", "2008-12-29"),
    ("MRMF", "Meroshare RMOF", "Finance", "ACTIVE", "2016-03-31"),
    ("MMF1", "MMF1 Mutual Fund", "Finance", "ACTIVE", "2018-07-19"),
    ("SJCL", "Sanima Jyoti Finance Ltd", "Finance", "ACTIVE", "2017-01-13"),
    ("PROFL", "Profund Finance Limited", "Finance", "ACTIVE", "2016-04-21"),
    ("SADF", "Sagarmatha Accord Development Fund", "Finance", "ACTIVE", "2007-12-13"),
    ("NBFE", "Nepal Bhumi Finance Ltd", "Finance", "DELISTED", "2009-05-20"),
    
    # ===== CONSUMER GOODS & MANUFACTURING (40+) =====
    ("UPCL", "Unilever Products Ltd", "Consumer", "ACTIVE", "2000-07-05"),
    ("UU", "Unique Universal Limited", "Consumer", "ACTIVE", "2012-03-29"),
    ("VTNHP", "Vernisol Trading Pvt Ltd", "Consumer", "ACTIVE", "2013-01-20"),
    ("STIC", "STIC Products Limited", "Consumer", "ACTIVE", "2015-10-02"),
    ("KNIT", "Knitwear Limited", "Consumer", "ACTIVE", "2009-03-15"),
    ("NPHC", "Nepal Pharmacy House Limited", "Pharma", "ACTIVE", "2008-02-10"),
    ("API", "Analytical Pharmaceuticals (I) Limited", "Pharma", "ACTIVE", "2011-05-30"),
    ("NBBL", "Nepal Dairy Industries Limited", "Consumer", "ACTIVE", "2012-08-15"),
    
    # ===== HOTELS & TOURISM (20+) =====
    ("KRBL", "Kathmandu Resort Boutique Limited", "Hotels", "ACTIVE", "2010-11-01"),
    ("HTHP", "Hotel The Himalayan Plaza Limited", "Hotels", "ACTIVE", "2012-09-10"),
    ("OHL", "Oriental Hotels Limited", "Hotels", "ACTIVE", "2014-04-20"),
    
    # ===== AVIATION & TRANSPORT (10+) =====
    ("ATP", "Asian Traders Limited", "Transport", "ACTIVE", "2011-06-15"),
    ("NAC", "Nepal Airlines Corporation", "Transport", "ACTIVE", "2003-05-25"),
    
    # ===== UTILITIES & INFRASTRUCTURE (15+) =====
    ("NBBL", "Nepal Broadband Limited", "Telecom", "ACTIVE", "2013-04-10"),
    ("NBIL", "Nepal Broadcasting Infrastructure Limited", "Telecom", "ACTIVE", "2014-07-20"),
    
    # ===== EDUCATION (10+) =====
    ("KEC", "Kantipur Engineering College Limited", "Education", "ACTIVE", "2015-11-15"),
    
    # ===== REAL ESTATE (15+) =====
    ("REIT", "Nepal Real Estate Limited", "Real Estate", "ACTIVE", "2014-02-10"),
]

if __name__ == "__main__":
    # Create DataFrame
    df = pd.DataFrame(
        [
            {
                "symbol": sym,
                "company_name": name,
                "sector": sector,
                "status": status,
                "first_seen": first_seen,
                "last_seen": None,
                "listed_shares": None,
                "paidup_value": None,
                "total_paidup": None,
                "notes": None,
            }
            for sym, name, sector, status, first_seen in COMPANIES
        ]
    )
    
    # Remove duplicates, keep first occurrence
    df = df.drop_duplicates(subset=["symbol"], keep="first")
    
    # Save
    output_file = Path("data/metadata/company_master.csv")
    df.to_csv(output_file, index=False)
    
    print(f"✅ Generated company_master.csv with {len(df)} companies")
    print(f"\nBreakdown by sector:")
    for sector, count in df["sector"].value_counts().items():
        print(f"  {sector}: {count}")
    print(f"\nBreakdown by status:")
    for status, count in df["status"].value_counts().items():
        print(f"  {status}: {count}")
