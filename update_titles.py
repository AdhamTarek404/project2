import re

with open('dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r'st\.title\("([^"]+)"\)',
    r'st.markdown("<h1 class=\'glitch-text\' data-text=\'\1\'>\1</h1>", unsafe_allow_html=True)',
    text
)

with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
