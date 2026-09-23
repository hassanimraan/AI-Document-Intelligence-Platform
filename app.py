import streamlit as st

st.set_page_config(page_title='Credential Extraction Assistant', page_icon='📄', layout='wide')

if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 'welcome'

st.markdown('## 📄 Credential Extraction Assistant')
st.write('Production-grade document extraction and persistent personal database.')

st.info('Phase 1 — Project Foundation')

col1, col2, col3, col4 = st.columns(4)
with col1: st.success('✓ Streamlit')
with col2: st.info('○ Gemini')
with col3: st.info('○ Supabase')
with col4: st.info('○ Excel Schema')

st.divider()
st.markdown('### 👋 Welcome')
st.write('The application will eventually authenticate users, recover their private workspace, process scanned PDFs with Gemini, allow human verification, save confirmed records to Supabase, and export the personal database to Excel.')

with st.sidebar:
    st.markdown('## 📊 My Database')
    st.info('Supabase authentication and persistent database will be connected in later phases.')
    st.metric('Confirmed Records', '0')
    st.divider()
    st.write('Version: `0.1.0`')

if st.button('Start Development Preview', type='primary', use_container_width=True):
    st.session_state.current_stage = 'upload'
    st.rerun()

if st.session_state.current_stage == 'upload':
    st.markdown('### 📤 Document Upload Preview')
    uploaded_file = st.file_uploader('Upload a PDF document', type=['pdf'])
    if uploaded_file:
        st.success(f'File received: {uploaded_file.name}')
        st.info('Gemini PDF processing will be added in the next phase.')
