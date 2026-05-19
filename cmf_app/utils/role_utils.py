"""
Utility functions for user role management.
Retrieves and calculates user roles from database.
"""

from db_sqlite import get_connection

def get_user_role(user_id: int) -> str:
    """
    Récupère le rôle principal de l'utilisateur depuis la base SQLite.
    
    Priorité de recherche :
    1. Champ 'role' dans app_users (rôle global de l'utilisateur)
    2. Rôle dans user_project_roles avec user_id (fallback pour rôles par projet)
    
    Retour :
        Le rôle principal "BUYER", "CAPACITY_MANAGER", "SQD", "ADMIN", ou "SUPER_ADMIN"
        Fallback : "BUYER" si aucun rôle trouvé
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # ===== ÉTAPE 1: Chercher dans app_users =====
        cursor.execute("SELECT role FROM app_users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row and row["role"]:
            role = str(row["role"]).strip().upper()
            conn.close()
            print(f"DEBUG: get_user_role({user_id}) found in app_users: {role}")
            return role
        
        # ===== ÉTAPE 2: Chercher dans user_project_roles =====
        cursor.execute("""
            SELECT DISTINCT role FROM user_project_roles
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            roles = [str(r["role"]).strip().upper() for r in rows]
            
            # Appliquer la priorité des rôles
            priority = ["SUPER_ADMIN", "ADMIN", "CAPACITY_MANAGER", "SQD", "BUYER"]
            for role_priority in priority:
                if role_priority in roles:
                    print(f"DEBUG: get_user_role({user_id}) found in user_project_roles: {role_priority}")
                    return role_priority
            
            # Retourner le premier rôle trouvé si aucun de la priorité
            print(f"DEBUG: get_user_role({user_id}) found in user_project_roles: {roles[0]}")
            return roles[0]
        
        # ===== FALLBACK: Aucun rôle trouvé =====
        print(f"DEBUG: get_user_role({user_id}) NO ROLE FOUND - returning BUYER as default")
        return "BUYER"
    
    except Exception as e:
        print(f"ERROR in get_user_role({user_id}): {e}")
        import traceback
        traceback.print_exc()
        return "BUYER"
