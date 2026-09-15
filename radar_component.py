"""Streamlit component bridge for same-server product page verification."""
import tempfile
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from radar import verify_radar

def render_radar(html):
    # Only the HTML is served; never expose the repository or its secrets.
    if '_radar_dir' not in st.session_state:
        st.session_state['_radar_dir'] = tempfile.mkdtemp(prefix='radar-ui-')
    folder = Path(st.session_state['_radar_dir'])
    target = folder / 'index.html'
    if not target.exists() or target.read_text(encoding='utf-8') != html:
        target.write_text(html, encoding='utf-8')
    component = components.declare_component('verified_radar', path=str(folder))
    response = st.session_state.get('_radar_response')
    request = component(response=response, key='verified_radar_ui', default=None)
    if isinstance(request, dict) and request.get('id') and request.get('id') != (response or {}).get('id'):
        query = request.get('productName')
        if isinstance(query, str) and 1 < len(query) <= 200:
            rows = verify_radar(query, request.get('candidates'))
            st.session_state['_radar_response'] = {'id': request['id'], 'rows': rows}
            st.rerun()
