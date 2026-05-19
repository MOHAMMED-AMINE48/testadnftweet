"""
Utilitaires et helpers pour l'application CMF.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime


class CMFHelpers:
    """Collection d'utilitaires pour CMF"""
    
    @staticmethod
    def format_capacity(capacity: float) -> str:
        """Formate une capacité pour affichage"""
        if capacity <= 0:
            return "—"
        return f"{capacity:.2f} parts/week"
    
    @staticmethod
    def format_status(status: str) -> str:
        """Formate un statut pour affichage"""
        status_map = {
            "PRESOURCING": "🔍 Presourcing",
            "ACTIVE": "✅ Active",
            "INACTIVE": "⏸️ Inactive",
            "PENDING": "⏳ Pending",
        }
        return status_map.get(status, status)
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """Formate une date"""
        if not date_str:
            return "—"
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return date_str
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Retourne la couleur du badge pour un statut"""
        status_colors = {
            "PRESOURCING": "#FFA500",  # Orange
            "ACTIVE": "#00AA00",       # Vert
            "INACTIVE": "#888888",     # Gris
            "PENDING": "#0066FF",      # Bleu
        }
        return status_colors.get(status, "#000000")
    
    @staticmethod
    def filter_records_by_status(records: List, status: str) -> List:
        """Filtre les records par statut"""
        return [r for r in records if r.status == status]
    
    @staticmethod
    def filter_records_by_supplier(records: List, supplier: str) -> List:
        """Filtre les records par fournisseur"""
        return [r for r in records if r.supplier_name == supplier]
    
    @staticmethod
    def get_unique_suppliers(records: List) -> List[str]:
        """Récupère la liste unique des fournisseurs"""
        suppliers = set()
        for record in records:
            if record.supplier_name:
                suppliers.add(record.supplier_name)
        return sorted(list(suppliers))
    
    @staticmethod
    def get_unique_sources(records: List) -> List[str]:
        """Récupère la liste unique des sources de capacité"""
        sources = set()
        for record in records:
            if record.capacity_source:
                sources.add(record.capacity_source)
        return sorted(list(sources))
    
    @staticmethod
    def calculate_total_capacity(records: List) -> float:
        """Calcule la capacité totale"""
        return sum(r.calculated_weekly_capacity for r in records if r.status == "ACTIVE")
    
    @staticmethod
    def create_records_dataframe(records: List) -> pd.DataFrame:
        """Convertit les records en DataFrame pour affichage"""
        data = []
        for record in records:
            data.append({
                "Part Number": record.part_number or "—",
                "Part Name": record.partname,
                "Supplier": record.supplier_name,
                "Quantity": f"{record.quantity}" if record.quantity > 0 else "—",
                "Status": CMFHelpers.format_status(record.status),
                "Capacity (parts/week)": CMFHelpers.format_capacity(record.calculated_weekly_capacity),
                "Source": record.capacity_source or "—",
                "Mix": f"{record.mix:.1%}" if record.mix else "—",
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def export_records_to_csv(records: List, output_file: str) -> bool:
        """Exporte les records en CSV"""
        try:
            df = CMFHelpers.create_records_dataframe(records)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Erreur export CSV: {e}")
            return False


class ChartHelpers:
    """Utilitaires pour créer des graphiques"""
    
    @staticmethod
    def prepare_capacity_by_supplier(records: List) -> Dict[str, float]:
        """Prépare les données pour graphique capacité par fournisseur"""
        data = {}
        for record in records:
            if record.status == "ACTIVE" and record.supplier_name:
                if record.supplier_name not in data:
                    data[record.supplier_name] = 0
                data[record.supplier_name] += record.calculated_weekly_capacity
        return dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def prepare_status_distribution(records: List) -> Dict[str, int]:
        """Prépare les données pour graphique de distribution des statuts"""
        from config.settings import RecordStatus
        
        data = {status.value: 0 for status in RecordStatus}
        for record in records:
            data[record.status] = data.get(record.status, 0) + 1
        return data
    
    @staticmethod
    def prepare_capacity_by_source(records: List) -> Dict[str, float]:
        """Prépare les données pour graphique capacité par source"""
        data = {}
        for record in records:
            if record.status == "ACTIVE" and record.capacity_source:
                if record.capacity_source not in data:
                    data[record.capacity_source] = 0
                data[record.capacity_source] += record.calculated_weekly_capacity
        return dict(sorted(data.items(), key=lambda x: x[1], reverse=True))


class ValidationHelpers:
    """Utilitaires pour les validations UI"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Valide un email simple"""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Valide une URL"""
        import re
        pattern = r'https?://.*'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Nettoie une chaîne de caractères"""
        if not isinstance(value, str):
            return ""
        return value.strip()
    
    @staticmethod
    def validate_numeric(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """Valide une valeur numérique"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
