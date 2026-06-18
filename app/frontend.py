import streamlit as st
import requests
import time
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AWS Contract Audit Dashboard", layout="wide")

st.title(" AWS Legal Contract Analyzer & System Analytics")
st.caption("Compliance auditing interface backed by Gemini-2.5 and local FAISS vector indexing maps.")

col_terminal, col_telemetry = st.columns([3, 2])

with col_terminal:
    st.subheader("Auditing Console")
    
    if st.button(" Initialize Document Ingestion Pipeline", use_container_width=True):
        with st.spinner("Processing PDF chunks and initializing FAISS matrices..."):
            try:
                res = requests.post(f"{BACKEND_URL}/ingest")
                if res.status_code == 200:
                    st.success(res.json().get("message"))
                else:
                    st.error(f"Ingestion rejected: {res.text}")
            except Exception as e:
                st.error(f"Backend offline or connection refused: {str(e)}")

    st.markdown("---")
    
    user_query = st.text_input("Submit Inquiry Targeting AWS Legal Document Constraints:", placeholder="e.g., What interest rate does AWS charge on late payments?")
    
    if st.button(" Execute Contract Retrieval Search", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a valid text inquiry.")
        else:
            with st.spinner("Searching document vector embeddings..."):
                try:
                    payload = {"query": user_query.strip()}
                    response = requests.post(f"{BACKEND_URL}/ask", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown("###  Auditor Determination:")
                        st.info(data["answer"])
                        st.markdown(f" **Pipeline Runtime Latency:** `{data['latency_seconds']:.4f} seconds`")
                        
                        with st.expander(" View Context Blocks Matched by FAISS"):
                            for idx, source_chunk in enumerate(data["sources"], 1):
                                st.markdown(f"**Context Fragment [{idx}]:**")
                                st.code(source_chunk, language="text")
                    else:
                        st.error(f"Error from server engine: Code {response.status_code}")
                except Exception as err:
                    st.error(f"Failed to communicate with API backend: {str(err)}")

with col_telemetry:
    st.subheader("Operational Telemetry")
    
    with st.expander(" Telemetry Simulation Controls"):
        if st.button(" Populate Metrics Logs (Automate 30 Contractual Queries)"):
            mock_queries = [
                "What interest rate does AWS charge on late payments?",
                "What happens if payment terms are violated?",
                "What is the late payment fee constraint?",
                "What is the duration limit to settle invoices?",
                "Can AWS suspend services for non-payment?",
                "What are the notice requirements prior to service termination?",
                "Does AWS offer indemnification coverage clauses?",
                "What is the limitation of liability financial cap?",
                "Which state or country laws govern this contract agreement?",
                "How is confidential data protected under the agreement clauses?",
                "Who owns the intellectual property of software modifications?",
                "What constitutes an event of Force Majeure under the legal contract?",
                "How can a customer formally terminate their active AWS service account?",
                "What are the remediation terms if service levels drop?",
                "Does this contract cover European Union data protection guidelines?",
                "Who is winning the football match tournament tonight?",
                "What is the weather forecast for tomorrow morning?",
                "Can you recommend a recipe for preparing pasta?",
                "Who founded FC Barcelona?",
                "What is the current trading price of bitcoin?",
                "What are the definitions of AWS Intellectual Property?",
                "Does AWS guarantee service availability under this agreement?",
                "Are there taxes included in the listed service fees?",
                "How are non-English contract variations handled?",
                "What is the effective date of this customer agreement?",
                "Can I assign this contract to a third party company?",
                "What constitutes a material breach under Section 5?",
                "How does AWS handle offline diagnostic hardware drives?",
                "What is the notice period for modifying service terms?",
                "Who won the cricket match yesterday afternoon?"
            ]
            
            bar = st.progress(0)
            status_lbl = st.empty()
            total = len(mock_queries)
            
            for index, query_item in enumerate(mock_queries):
                status_lbl.text(f"Logging telemetry loop [{index + 1}/{total}]")
                try:
                    requests.post(f"{BACKEND_URL}/ask", json={"query": query_item})
                except:
                    pass
                bar.progress((index + 1) / total)
                time.sleep(0.02)
                
            st.success("Telemetry log matrix compiled. Refreshing analytics panel.")
            time.sleep(0.5)
            st.rerun()

    try:
        analytics_response = requests.get(f"{BACKEND_URL}/analytics")
        if analytics_response.status_code == 200:
            metrics = analytics_response.json()
            
            
            st.metric("Total API Requests Logged", metrics.get("total_queries", 0))
            st.metric("Out-of-Scope Fallbacks Triggered", metrics.get("unanswered_queries_count", 0))
            st.metric("Mean Pipeline Latency", f"{metrics.get('average_latency_seconds', 0.0):.4f} sec")
            
            trends = metrics.get("most_frequent_queries", [])
            if trends:
                st.markdown(" **Top System Query Trends:**")
                for item in trends:
                    st.caption(f"Hits: `{item.get('count', 0)}` | *\"{item.get('query', '')}\"*")
            else:
                st.caption("No log entries processed yet. Run queries to compile metrics trends.")
        else:
            st.caption("Unable to communicate with metrics server aggregation layout.")
    except Exception:
        st.caption("Waiting for backend API node to stream pipeline statistics...")