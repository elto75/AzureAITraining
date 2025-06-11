#!/bin/bash

pip install streamlit
pip install dotenv
pip install openai

python -m streamlit run 01.rag-streamlit.py --server.port 8000