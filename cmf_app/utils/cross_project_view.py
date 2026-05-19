import pandas as pd
import streamlit as st


def render_cross_project_view(cmf_repo) -> None:
    """Render the cross-project part number view."""
    st.subheader("Component Cross-Project View")
    st.write(
        "For each Part Number registered across all CMF projects, "
        "shows whether it is **New** (not yet in any project) or already "
        "present in one or more projects."
    )

    try:
        all_projects = cmf_repo.get_all_projects_for_cross_view()

        if not all_projects:
            st.info("No projects found in the database.")
            return

        cross_data = cmf_repo.get_cross_project_part_number_view()

        if not cross_data:
            st.info("No part numbers found across any project.")
            return

        project_labels = {
            project["id"]: f"{project['code']} - {project['name']}" if project.get("name") else project["code"]
            for project in all_projects
        }

        display_rows = []
        for entry in cross_data:
            project_count = sum(1 for proj in all_projects if entry.get(f"proj_{proj['id']}", False))
            row = {
                "APQP": entry.get("apqp") or "—",
                "Part Name": entry.get("part_name") or "—",
                "Part Number": entry.get("part_number") or "—",
            }
            row["CarryOver - Adapted"] = "Adapted" if project_count == 1 else "CarryOver"
            for proj in all_projects:
                row[project_labels[proj["id"]]] = entry.get(f"proj_{proj['id']}", False)
            display_rows.append(row)

        df_cross = pd.DataFrame(display_rows)

        total_pn = len(df_cross)
        project_columns = [project_labels[project["id"]] for project in all_projects]
        shared_pn = int((df_cross[project_columns].sum(axis=1) > 1).sum()) if len(all_projects) > 1 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Part Numbers", total_pn)
        with col2:
            st.metric("Unique components", int((df_cross[project_columns].sum(axis=1) == 1).sum()) if len(all_projects) > 0 else 0)
        with col3:
            st.metric("Shared across projects", shared_pn)
        with col4:
            st.metric("Projects", len(all_projects))

        st.divider()

        search_pn = st.text_input("Search Part Number / Part Name", "")

        df_view = df_cross.copy()
        if search_pn.strip():
            mask = (
                df_view["Part Number"].str.contains(search_pn, case=False, na=False)
                | df_view["Part Name"].str.contains(search_pn, case=False, na=False)
            )
            df_view = df_view[mask]

        st.write(f"Showing **{len(df_view)}** of **{total_pn}** part numbers")

        for project in all_projects:
            df_view[project_labels[project["id"]]] = df_view[project_labels[project["id"]]].astype(bool)

        col_config = {}
        for project in all_projects:
            project_label = project_labels[project["id"]]
            col_config[project_label] = st.column_config.CheckboxColumn(
                project_label,
                help=f"Checked = Part Number exists in project {project['name']}",
                default=False,
            )

        st.dataframe(
            df_view.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            column_config=col_config,
        )

        st.divider()

        csv_cross = df_view.to_csv(index=False)
        st.download_button(
            label="Download Cross-Project View as CSV",
            data=csv_cross,
            file_name="cross_project_parts.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error loading cross-project view: {str(e)}")
        import traceback
        traceback.print_exc()


def get_cross_project_part_numbers(cmf_repo):
    """Return a set of all part numbers present across projects (normalized)."""
    try:
        cross_data = cmf_repo.get_cross_project_part_number_view()
        shared = set()
        for entry in cross_data:
            pn = (entry.get("part_number") or "").strip()
            if not pn:
                continue
            # Count how many project presence flags are True (keys like proj_<id>)
            proj_count = 0
            for k, v in entry.items():
                if k.startswith("proj_") and v:
                    proj_count += 1
            # Consider it a shared (CO) part number only when present in more than one project
            if proj_count > 1:
                shared.add(pn)
        return shared
    except Exception:
        return set()
