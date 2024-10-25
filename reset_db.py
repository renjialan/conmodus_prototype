import streamlit as st
from fix_retriever import reset_chroma

if __name__ == "__main__":
    st.write("Starting ChromaDB initialization...")
    
    # Add a spinner to show progress
    with st.spinner('Initializing ChromaDB...'):
        try:
            store = reset_chroma()
            if store:
                st.success("ChromaDB successfully initialized!")
            else:
                st.error("Failed to initialize ChromaDB. Check the error messages below.")
                st.write(st.session_state.get('error_message', 'No error message available.'))
        except Exception as e:
            st.error(f"Error during initialization: {str(e)}")
            st.exception(e)  # This will show the full traceback

    # Display any print statements from reset_chroma
    if 'output' in st.session_state:
        st.write("Detailed output:")
        st.write(st.session_state.output)