import hashlib #Used to create a unique signature/fingerprint for uploaded CSV files.
import os
from pathlib import Path
import streamlit as st
import pandas as pd

from agent import run_agent


st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 AI Data Analyst")


if "messages" not in st.session_state:
    st.session_state.messages = []


if "message_artifacts" not in st.session_state:
    st.session_state.message_artifacts = {}


if "datasets" not in st.session_state:
    st.session_state.datasets = {}


if "file_signatures" not in st.session_state:
    st.session_state.file_signatures = []


if "pending_request" not in st.session_state:
    st.session_state.pending_request = None

#Creates the artifact directory if it does not exist; repeated runs are safe because exist_ok=True is used.

Path("artifacts/charts").mkdir( 
    parents=True,
    exist_ok=True
)

Path("artifacts/reports").mkdir(
    parents=True,
    exist_ok=True
)


def render_message(message, artifacts, message_index):
    
    #Create the correct chat bubble and put the message text inside it.
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        for chart_number, chart_path in enumerate( #enumerate() gives each item a number.
            artifacts.get("chart_paths", [])
        ):
            if os.path.exists(chart_path):
                st.image(
                    chart_path,
                    width="stretch"
                )
                
        #Find all PDF reports connected to this chat message.Take them one by one.Check if each PDF exists.Open the PDF.Create a download button.Give Streamlit the PDF data.Give thedownloaded file its proper filename.Make the button unique.
        for report_number, report_path in enumerate(
            artifacts.get("report_paths", [])
        ):
            if os.path.exists(report_path):
                with open(report_path, "rb") as file:
                    st.download_button(
                        "⬇️ Download Report",
                        data=file.read(),
                        file_name=Path(report_path).name,
                        mime="application/pdf",
                        width="stretch",
                        key=(
                            f"download_"
                            f"{message_index}_"
                            f"{report_number}_"
                            f"{Path(report_path).name}"
                        )
                    )


with st.sidebar:
    st.header("📁 Files")

    if st.button(
        "🆕 New Chat",
        width="stretch"
    ):
        st.session_state.messages = []
        st.session_state.message_artifacts = {}
        st.rerun()

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload CSV files",
        type=["csv"],
        accept_multiple_files=True
    )

    #These are temporary variables.
    new_datasets = {}
    signatures = []

    for uploaded_file in uploaded_files:
        try:
             #Get the raw contents of the uploaded CSV and store them in raw.
            raw = uploaded_file.getvalue()

            #The program needs a way to recognize whether the uploaded files have changed
            signature = (
                uploaded_file.name,
                len(raw), #len(raw) tells you how many bytes are in that file.
                hashlib.md5(raw).hexdigest() #This creates a kind of fingerprint of the file contents.
            )
            
            #signature = (
            #     "sales.csv",
            #     48291,
            #     "a7f8c91d..."
            # )

            signatures.append(signature)

            new_datasets[uploaded_file.name] = pd.read_csv(
                uploaded_file
            )

        except Exception as e:
            st.error(
                f"Could not read {uploaded_file.name}: {e}"
            )

    signatures = sorted(signatures)

    if signatures != st.session_state.file_signatures: #Are the files currently uploaded different from the files we previously stored?
        st.session_state.file_signatures = signatures
        st.session_state.datasets = new_datasets
        
        #Clear/reset the stored charts/PDF associations
        st.session_state.messages = []
        st.session_state.message_artifacts = {}

    if st.session_state.datasets:
        st.success(
            f"{len(st.session_state.datasets)} CSV file(s) loaded"
        )

        for name, df in st.session_state.datasets.items():
            if len(df) == 0:
                st.warning(
                    f"📄 {name} · 0 rows · {len(df.columns)} columns"
                )
            else:
                st.caption(
                    f"📄 {name} · "
                    f"{len(df):,} rows · "
                    f"{len(df.columns)} columns"
                )

        st.divider()

        if st.button(
            "📄 Overall Report",
            width="stretch"
        ):
            st.session_state.pending_request = (
                "Create a complete overall PDF report using "
                "all uploaded CSV files. Analyze every non-empty "
                "dataset, ignore empty datasets, create a small "
                "number of useful charts, and generate the final "
                "downloadable PDF report."
            )
            st.rerun()

    else:
        st.info(
            "Upload one or more CSV files to start."
        )


if st.session_state.datasets:

    with st.expander("📊 View uploaded datasets"):
        tabs = st.tabs(
            list(st.session_state.datasets.keys())
        )

        for tab, (name, df) in zip(
            tabs,
            st.session_state.datasets.items()
        ):
            with tab:
                st.dataframe(
                    df,
                    width="stretch"
                )

                st.caption(
                    f"{len(df):,} rows · "
                    f"{len(df.columns)} columns"
                )

    for index, message in enumerate(
        st.session_state.messages
    ):
        render_message(
            message,
            st.session_state.message_artifacts.get(
                index,
                {}
            ),
            index
        )

    user_query = st.chat_input(
        "Ask anything about your data..."
    )

    request = (
        st.session_state.pending_request
        or user_query
    )

    if st.session_state.pending_request:
        st.session_state.pending_request = None

    if request:
        st.session_state.messages.append({
            "role": "user",
            "content": request
        })

        with st.chat_message("user"):
            st.markdown(request)

        with st.chat_message("assistant"):
            with st.status(
                "🤖 Agent is working...",
                expanded=True
            ) as status:

                def update_status(message):
                    status.write(message)
                    status.update(
                        label=message,
                        state="running"
                    )

                (
                    answer,
                    chart_paths,
                    report_paths
                ) = run_agent(
                    st.session_state.datasets,
                    st.session_state.messages,
                    status_callback=update_status
                )

                status.update(
                    label="✅ Completed",
                    state="complete",
                    expanded=False
                )

            st.markdown(answer)

            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    st.image(
                        chart_path,
                        width="stretch"
                    )

            for report_number, report_path in enumerate(
                report_paths
            ):
                if os.path.exists(report_path):
                    with open(report_path, "rb") as file:
                        st.download_button(
                            "⬇️ Download Report",
                            data=file.read(),
                            file_name=Path(report_path).name,
                            mime="application/pdf",
                            width="stretch",
                            key=(
                                f"new_download_"
                                f"{len(st.session_state.messages)}_"
                                f"{report_number}_"
                                f"{Path(report_path).name}"
                            )
                        )

        assistant_index = len(
            st.session_state.messages
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.session_state.message_artifacts[
            assistant_index
        ] = {
            "chart_paths": list(chart_paths),
            "report_paths": list(report_paths)
        }

else:
    st.info(
        "Upload one or more CSV files to start analyzing."
    )
