mkdir -p ~/.streamlit/
echo "\ 
[servidor]\n\ 
sin cabeza = verdadero\n\ 
puerto = $PORT\n\ 
enableCORS = falso\n\ 
\n\ 
" > ~/.streamlit/config.toml