from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent
FAIRS_DIR = HUB_ROOT / "fairs"
MASTER_PATH = HUB_ROOT / "output" / "Career_Fair_Master.xlsx"

BATCH_SIZE = 15

# key, label, dark colour, light colour
CATEGORIES = [
    ("job", "Job / Internship Booth", "1F4E78", "DDEBF7"),
    ("further", "Further Study", "548235", "E2EFDA"),
    ("startup", "Entrepreneurship & Startup", "C55A11", "FCE4D6"),
    ("other", "Other Exhibitor (no apply details)", "7F6000", "FFF2CC"),
    ("career", "Career Support / Activity", "7030A0", "E4DFEC"),
    ("sponsor", "Merchandise / F&B Sponsor", "595959", "EDEDED"),
]
CATEGORY = {k: (label, dark, light) for k, label, dark, light in CATEGORIES}
SHARE_CATEGORIES = ("job", "further", "startup")
TRACKABLE_CATEGORIES = ("job", "further", "startup", "other")

STATUSES = ["Not Applied", "Planning to Apply", "Applied", "Assessment / Test", "Interview", "Offer", "Accepted",
            "Rejected", "Withdrawn", "Not Applying"]
STATUS_FILL = {"Planning to Apply": "FFF2CC", "Applied": "BDD7EE", "Assessment / Test": "D9E1F2",
               "Interview": "F8CBAD", "Offer": "C6EFCE", "Accepted": "70AD47", "Rejected": "FFC7CE",
               "Withdrawn": "D9D9D9", "Not Applying": "D9D9D9"}
IN_PROGRESS = ("Planning to Apply", "Applied", "Assessment / Test", "Interview")
APPLIED_VIA = ["QR / Online Form", "Email", "Career Portal", "LinkedIn", "Job Board (JobStreet etc.)",
               "At the Booth", "Referral"]

# Tracker columns in the master workbook — preserved across rebuilds
TRACK_COLUMNS = [
    ("Interested?", 11), ("Priority", 10), ("Application Status", 16), ("Position / Programme Applied For", 26),
    ("Applied Via", 16), ("Applied Date", 12), ("Follow-up Date", 12), ("Response / Last Update", 26),
    ("Interview Date", 12), ("Next Action", 24), ("My Notes", 30),
]
DATE_COLUMNS = ("Applied Date", "Follow-up Date", "Interview Date")

# Link destinations that mean a QR code has expired / is dead
DEAD_LINK_MARKERS = ["me-qr.com/blog", "me-qr.com/ja/blog", "me-qr.com/id/blog", "me-qr.com/pricing"]
