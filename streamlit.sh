#!/bin/bash

pip install streamlit
pip install dotenv
pip install openai

python -m streamlit run chatbot_agent.py --server.port 8000