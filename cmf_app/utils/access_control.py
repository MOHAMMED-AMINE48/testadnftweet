"""
Centralized access control for role-based page access.
Defines which roles can access which pages.
"""

import streamlit as st

# Map de pages et les rôles autorisés
ROLE_PAGE_MAP = {
    "buyer":            ["BUYER", "ADMIN"],
    "capacity_manager": ["CAPACITY_MANAGER", "ADMIN"],
    "sqd":              ["SQD", "ADMIN"],
    "cross_project":    ["BUYER", "CAPACITY_MANAGER", "SQD", "ADMIN"],
    "admin_users":      ["ADMIN"],
}


def require_auth(page_key: str):
    """
    Vérifie que l'utilisateur est connecté et a le bon rôle pour accéder à la page.
    
    Args:
        page_key: Clé de la page ('buyer', 'capacity_manager', 'sqd', 'cross_project', 'admin_users')
    
    Raises:
        Affiche un message d'erreur et arrête l'exécution si l'utilisateur n'a pas accès
    """
    # Vérifier l'authentification
    if not st.session_state.get("is_authenticated"):
        st.warning("You must be logged in to access this page.")
        st.stop()
    
    # Récupérer le rôle de l'utilisateur
    user_role = st.session_state.get("user_role", "")
    
    # Récupérer les rôles autorisés pour cette page
    allowed_roles = ROLE_PAGE_MAP.get(page_key, [])
    
    # Vérifier le rôle
    if user_role not in allowed_roles:
        error_msg = (
            f"Access Denied. This page is for "
            f"{', '.join(allowed_roles)} only. "
            f"Your role: {user_role}"
        )
        st.error(error_msg)
        st.stop()


def show_debug_session():
    """
    Affiche le state de debug temporaire (à utiliser pendant les tests).
    """
    st.write("DEBUG session_state :", {
        "is_authenticated": st.session_state.get("is_authenticated"),
        "user_role": st.session_state.get("user_role"),
        "current_user_email": st.session_state.get("current_user_email"),
        "current_user_id": st.session_state.get("current_user_id"),
    })
