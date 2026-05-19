"""
Gestionnaire d'encodage pour gérer les données avec encodages mixtes.
Résout les problèmes de décodage UTF-8 incomplets.
"""

from typing import Any, Dict, List


def safe_decode_value(value: Any) -> Any:
    """
    Décode une valeur de manière sûre, en essayant plusieurs encodages.
    
    Args:
        value: La valeur à décoder (peut être bytes, str, ou autre type)
        
    Returns:
        La valeur décodée (str si c'était du texte, ou la valeur originale)
    """
    # Si ce n'est pas des bytes ou une string, retourner tel quel
    if value is None:
        return value
    
    if isinstance(value, (int, float, bool)):
        return value
    
    # Si c'est déjà une string valide UTF-8, retourner tel quel
    if isinstance(value, str):
        # Vérifier que c'est bien du UTF-8 valide
        try:
            value.encode('utf-8')
            return value
        except UnicodeEncodeError:
            # Si ce n'est pas du UTF-8 valide, essayer de le réencoder
            try:
                # Essayer d'interpréter comme Latin-1 puis encoder en UTF-8
                return value.encode('latin-1').decode('utf-8', errors='replace')
            except Exception:
                return str(value)
    
    # Si c'est des bytes
    if isinstance(value, bytes):
        # Essayer UTF-8 d'abord
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            pass
        
        # Essayer Latin-1
        try:
            return value.decode('latin-1')
        except UnicodeDecodeError:
            pass
        
        # Essayer Windows-1252
        try:
            return value.decode('windows-1252')
        except UnicodeDecodeError:
            pass
        
        # En dernier recours, utiliser replace pour ignorer les caractères invalides
        return value.decode('utf-8', errors='replace')
    
    # Pour tout autre type, convertir en string
    try:
        return str(value)
    except Exception:
        return repr(value)


def clean_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Nettoie une liste de records en décodant toutes les valeurs problématiques.
    
    Args:
        records: Liste de dictionnaires (records de la base)
        
    Returns:
        Liste de dictionnaires avec tous les problèmes d'encodage résolus
    """
    if not records:
        return records
    
    cleaned = []
    for record in records:
        cleaned_record = {}
        for key, value in record.items():
            cleaned_record[key] = safe_decode_value(value)
        cleaned.append(cleaned_record)
    
    return cleaned


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie un seul record en décodant toutes les valeurs problématiques.
    
    Args:
        record: Dictionnaire (record de la base)
        
    Returns:
        Dictionnaire avec tous les problèmes d'encodage résolus
    """
    if not record:
        return record
    
    cleaned_record = {}
    for key, value in record.items():
        cleaned_record[key] = safe_decode_value(value)
    
    return cleaned_record
