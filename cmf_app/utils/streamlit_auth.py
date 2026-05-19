"""
Streamlit authentication UI components and logic.
Handles user login and session management.
"""
import streamlit as st
from repositories.user_repository_sqlite import UserRepository
from utils.auth import verify_password
from utils.role_utils import get_user_role


def show_login_form():
    """
    Display the login form and handle authentication.
    Sets session state variables upon successful login.
    """
    st.title("Capacity Management")
    st.caption("CMF Platform - Professional Authentication")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Login")

        # Login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email Address",
                placeholder="user@company.com",
                help="Enter your email address"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Enter your password"
            )

            submit = st.form_submit_button(
                "Login",
                use_container_width=True,
                type="primary"
            )

        if submit:
            if not email or not password:
                st.error("Email and password are required.")
            else:
                # Verify credentials
                repo = UserRepository()
                user = repo.get_user_by_email(email)

                if not user:
                    st.error("Email address not found.")
                elif not verify_password(password, user.password_hash):
                    st.error("Password is incorrect.")
                else:
                    # Authentication successful
                    st.session_state["is_authenticated"] = True
                    st.session_state["current_user_id"] = int(user.id)
                    st.session_state["current_user_email"] = user.email
                    st.session_state["current_user_name"] = user.full_name or email

                    # Récupérer le rôle principal de l'utilisateur
                    user_role = get_user_role(int(user.id))
                    st.session_state["user_role"] = user_role
                    st.session_state["current_user"] = email  # For compatibility

                    # Afficher les informations de connexion avec le rôle
                    st.success(f"Login successful. Role: {user_role}")
                    st.info(f"Welcome {user.full_name or email} ({user_role})")
                    st.rerun()

        st.divider()
        st.caption("Capacity Management Platform")
        st.caption("Secure • Audit Trail • Enterprise")


def require_authentication():
    """
    Decorator-like function to check if user is authenticated.
    If not, displays warning and stops execution.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    if not st.session_state.get("is_authenticated"):
        st.warning("You must be logged in to access this page.")
        st.info("Please use the login form to authenticate.")
        st.stop()
        return False
    return True


def logout():
    """
    Clear authentication session state.
    """
    st.session_state["is_authenticated"] = False
    st.session_state["current_user_id"] = None
    st.session_state["current_user_email"] = None
    st.session_state["current_user_name"] = None
    st.session_state["user_role"] = None
    st.session_state["current_user"] = None
    st.rerun()


def get_current_user_info():
    """
    Get information about the currently logged-in user.
    
    Returns:
        dict: User information or None
    """
    if not st.session_state.get("is_authenticated"):
        return None
    
    return {
        "id": st.session_state.get("current_user_id"),
        "email": st.session_state.get("current_user_email"),
        "name": st.session_state.get("current_user_name"),
        "role": st.session_state.get("user_role"),
    }
