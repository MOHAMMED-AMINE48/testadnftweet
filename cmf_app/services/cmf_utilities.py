"""
Multi-CMF utilities for Capacity Manager and SQD pages.
Provides helper functions for CMF selection, filtering, and context management.
"""

from typing import List, Optional
from models.project_schema import Project
from services.project_repository import JSONProjectRepository


def get_cmfs_for_capacity_manager(user_id: str) -> List[Project]:
    """
    Get all CMF projects assigned to a specific Capacity Manager.
    
    Args:
        user_id: Username of the Capacity Manager
    
    Returns:
        List of Project objects where capacity_manager_name == user_id
    """
    try:
        repo = JSONProjectRepository()
        all_cmfs = repo.get_all_projects()
        
        # Filter by capacity_manager_name
        assigned_cmfs = [
            cmf for cmf in all_cmfs
            if cmf.capacity_manager_name == user_id and cmf.is_active
        ]
        
        return assigned_cmfs
    except Exception as e:
        print(f"Error fetching CMFs for capacity manager {user_id}: {str(e)}")
        return []


def get_cmfs_for_sqd(user_id: str) -> List[Project]:
    """
    Get all CMF projects assigned to a specific SQD (Quality Manager).
    
    Args:
        user_id: Username of the SQD
    
    Returns:
        List of Project objects where sqd_assigned == user_id
    """
    try:
        repo = JSONProjectRepository()
        all_cmfs = repo.get_all_projects()
        
        # Filter by sqd_assigned
        assigned_cmfs = [
            cmf for cmf in all_cmfs
            if cmf.sqd_assigned == user_id and cmf.is_active
        ]
        
        return assigned_cmfs
    except Exception as e:
        print(f"Error fetching CMFs for SQD {user_id}: {str(e)}")
        return []


def get_cmfs_for_buyer(user_id: str) -> List[Project]:
    """
    Get all CMF projects assigned to a specific Buyer.
    
    Args:
        user_id: Username of the Buyer
    
    Returns:
        List of Project objects where buyer_assigned == user_id
    """
    try:
        repo = JSONProjectRepository()
        all_cmfs = repo.get_all_projects()
        
        # Filter by buyer_assigned
        assigned_cmfs = [
            cmf for cmf in all_cmfs
            if cmf.buyer_assigned == user_id and cmf.is_active
        ]
        
        return assigned_cmfs
    except Exception as e:
        print(f"Error fetching CMFs for buyer {user_id}: {str(e)}")
        return []


def format_cmf_option(cmf: Project) -> str:
    """
    Format a CMF for display in a selectbox.
    
    Args:
        cmf: Project object
    
    Returns:
        Formatted string like "CMF001 – Project Alpha (john_cm)"
    """
    cm_display = f" ({cmf.capacity_manager_name})" if cmf.capacity_manager_name else ""
    return f"{cmf.project_code} – {cmf.project_name}{cm_display}"
