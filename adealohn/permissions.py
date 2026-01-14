"""
Berechtigungen für AdeaLohn-Modul.
"""


def can_access_adelohn(user):
    """
    Prüft, ob der User auf AdeaLohn zugreifen kann.
    
    Aktuell: Alle authentifizierten Staff-User können zugreifen.
    Kann später erweitert werden für granulare Berechtigungen.
    """
    if not user or not user.is_authenticated:
        return False
    
    # Staff-User haben Zugriff
    if user.is_staff:
        return True
    
    # Kann später erweitert werden für spezifische Berechtigungen
    # z.B. per Group oder Permission
    return False








