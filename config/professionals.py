PROFESSIONALS: list[dict] = [
    {"id": "1", "name": "Dr. García",    "specialty": "Medicina General", "calendar_email": ""},
    {"id": "2", "name": "Dra. López",    "specialty": "Pediatría",        "calendar_email": ""},
    {"id": "3", "name": "Lic. Martínez", "specialty": "Psicología",       "calendar_email": ""},
]


def get_professionals_list() -> str:
    return "\n".join(f"{i}. {p['name']} — {p['specialty']}" for i, p in enumerate(PROFESSIONALS, 1))


def find_professional(text: str) -> dict | None:
    text_lower = text.strip().lower()
    try:
        idx = int(text_lower) - 1
        if 0 <= idx < len(PROFESSIONALS):
            return PROFESSIONALS[idx]
    except ValueError:
        pass
    for prof in PROFESSIONALS:
        if text_lower in prof["name"].lower():
            return prof
    return None
