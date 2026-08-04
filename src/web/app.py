import streamlit as st
import os
from pathlib import Path
import yaml
import pandas as pd
import base64
import json

st.set_page_config(page_title="Job Pipeline Dashboard", layout="wide")

st.sidebar.title("Job Pipeline")

users_dir = Path("users")
if not users_dir.exists():
    users_dir.mkdir(parents=True, exist_ok=True)

users = [d.name for d in users_dir.iterdir() if d.is_dir()]

if not users:
    st.warning("No users found. Please run the CLI to generate a user directory.")
    st.stop()

selected_user = st.sidebar.selectbox("Select User", users)
user_path = users_dir / selected_user

tab1, tab2, tab3 = st.tabs(["Dashboard", "Configuration", "Prompts"])

with tab1:
    st.header("Job Review & Match Analysis")

    tracker_path = user_path / "output" / "tracker.csv"
    if tracker_path.exists():
        try:
            df = pd.read_csv(tracker_path)

            # Kanban Board
            statuses = df['Status'].unique()
            if len(statuses) == 0:
                statuses = ["- [ ]"] # Default

            columns = st.columns(len(statuses) if len(statuses) > 0 else 1)

            for i, status in enumerate(statuses):
                with columns[i]:
                    st.subheader(status)
                    status_df = df[df['Status'] == status]

                    for index, row in status_df.iterrows():
                        with st.expander(f"{row['Company']} - {row['Title']}"):
                            st.write(f"**Location:** {row.get('Location', '')}")
                            st.write(f"**Match Score:** {row.get('Match Score', '')}")
                            st.write(f"**Salary:** {row.get('Salary', '')}")
                            if 'Link' in row and pd.notna(row['Link']):
                                st.write(f"**Link:** [Apply]({row['Link']})")

                            # Parse job slug
                            resume_path_str = str(row.get('Resume', ''))
                            job_slug = ""
                            if resume_path_str.startswith("output/") and "/resume.pdf" in resume_path_str:
                                job_slug = resume_path_str.split("/")[1]

                            if job_slug:
                                job_dir = user_path / "output" / job_slug
                                job_md_path = job_dir / "job.md"

                                if job_md_path.exists():
                                    with open(job_md_path, 'r', encoding='utf-8') as f:
                                        job_desc = f.read()
                                    with st.expander("Job Description"):
                                        st.markdown(job_desc)

                                # PDF Previewer
                                resume_pdf_path = job_dir / "resume.pdf"
                                if resume_pdf_path.exists():
                                    with open(resume_pdf_path, "rb") as f:
                                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                    with st.expander("Preview Resume PDF"):
                                        st.markdown(pdf_display, unsafe_allow_html=True)

                                cl_pdf_path = job_dir / "cover_letter.pdf"
                                if cl_pdf_path.exists():
                                    with open(cl_pdf_path, "rb") as f:
                                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                    with st.expander("Preview Cover Letter PDF"):
                                        st.markdown(pdf_display, unsafe_allow_html=True)

                            # Status update form (simplified for now)
                            new_status = st.selectbox("Update Status", ["- [ ]", "Applied", "Rejected", "Interview"], key=f"status_{index}", index=["- [ ]", "Applied", "Rejected", "Interview"].index(status) if status in ["- [ ]", "Applied", "Rejected", "Interview"] else 0)
                            if new_status != status:
                                df.at[index, 'Status'] = new_status
                                df.to_csv(tracker_path, index=False)
                                st.rerun()

        except Exception as e:
            st.error(f"Error reading tracker: {e}")
    else:
        st.info("No tracker.csv found. Run the pipeline to generate jobs.")


with tab2:
    st.header("Configuration Editor")
    config_path = user_path / "config.yaml"

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        with st.form("config_form"):
            st.subheader("Search Settings")
            search_data = config_data.get('search', {})

            keywords = st.text_input("Keywords", search_data.get('keywords', ''))
            location = st.text_input("Location", search_data.get('location', ''))
            remote = st.checkbox("Remote", search_data.get('remote', False))
            results_wanted = st.number_input("Results Wanted", value=search_data.get('results_wanted', 10), min_value=1)
            min_salary = st.number_input("Min Salary", value=search_data.get('min_salary', 0))

            exclude_companies_str = st.text_area("Exclude Companies (comma separated)", ", ".join(search_data.get('exclude_companies', [])))
            exclude_keywords_str = st.text_area("Exclude Keywords (comma separated)", ", ".join(search_data.get('exclude_keywords', [])))
            proxies_str = st.text_area("Proxies (comma separated)", ", ".join(search_data.get('proxies', [])))

            job_type = st.text_input("Job Type", search_data.get('job_type', ''))

            st.subheader("General Settings")
            provider = st.text_input("Provider", config_data.get('provider', 'openai'))
            model = st.text_input("Model", config_data.get('model', 'gpt-4o-mini'))
            base_resume = st.text_input("Base Resume Path", config_data.get('base_resume', ''))

            submitted = st.form_submit_button("Save Configuration")
            if submitted:
                config_data['search']['keywords'] = keywords
                config_data['search']['location'] = location
                config_data['search']['remote'] = remote
                config_data['search']['results_wanted'] = results_wanted
                config_data['search']['min_salary'] = min_salary if min_salary > 0 else None

                config_data['search']['exclude_companies'] = [c.strip() for c in exclude_companies_str.split(",")] if exclude_companies_str else []
                config_data['search']['exclude_keywords'] = [k.strip() for k in exclude_keywords_str.split(",")] if exclude_keywords_str else []
                config_data['search']['proxies'] = [p.strip() for p in proxies_str.split(",")] if proxies_str else []

                config_data['search']['job_type'] = job_type if job_type else None

                config_data['provider'] = provider
                config_data['model'] = model
                config_data['base_resume'] = base_resume

                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f)
                st.success("Configuration saved!")
    else:
        st.warning(f"No config.yaml found for user {selected_user}")

with tab3:
    st.header("Prompt & Base Resume Editor")

    # Base Resume
    config_path = user_path / "config.yaml"
    base_resume_content = ""
    base_resume_path = None

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        base_resume_rel_path = config_data.get('base_resume', '')
        if base_resume_rel_path:
            base_resume_path = user_path / base_resume_rel_path

            if base_resume_path.exists():
                with open(base_resume_path, 'r', encoding='utf-8') as f:
                    base_resume_content = f.read()
            else:
                st.warning(f"Base resume not found at {base_resume_path}")

    if base_resume_path:
        st.subheader("Base Resume")
        with st.form("base_resume_form"):
            new_base_resume = st.text_area("Edit Base Resume", base_resume_content, height=300)
            if st.form_submit_button("Save Base Resume"):
                with open(base_resume_path, 'w', encoding='utf-8') as f:
                    f.write(new_base_resume)
                st.success("Base Resume saved!")

    st.subheader("Prompts")
    prompts_dir = user_path / "prompts"
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True, exist_ok=True)

    prompt_files = list(prompts_dir.glob("*.md"))

    if prompt_files:
        selected_prompt = st.selectbox("Select Prompt to Edit", [p.name for p in prompt_files])
        prompt_path = prompts_dir / selected_prompt

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        with st.form("prompt_form"):
            new_prompt = st.text_area(f"Edit {selected_prompt}", prompt_content, height=300)
            if st.form_submit_button(f"Save {selected_prompt}"):
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(new_prompt)
                st.success(f"{selected_prompt} saved!")
    else:
        st.info("No custom prompts found in users/{user}/prompts/. To override default prompts, create files like resume.md, cover_letter.md, etc. in that directory.")

        new_prompt_name = st.text_input("Create new custom prompt (e.g., resume.md)")
        if st.button("Create"):
            if new_prompt_name:
                if not new_prompt_name.endswith('.md'):
                    new_prompt_name += '.md'
                new_path = prompts_dir / new_prompt_name
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write("")
                st.success(f"Created {new_prompt_name}! Refreshing...")
                st.rerun()
