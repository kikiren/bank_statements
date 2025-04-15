import streamlit as st
import pypdf
import re
import pandas as pd
import io

st.title("Chase Bank Statement Reader")

# File uploader
local_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if local_file is not None:
    st.write("Filename:", local_file.name)

    # Read and extract text from the uploaded PDF
    pdf_reader = pypdf.PdfReader(local_file)
    text = ""
    for page in pdf_reader.pages:
        try:
            text += page.extract_text()
        except Exception:
            continue

    # Extract the section of interest
    start_index = text.find("Transaction Merchant  Name or Transaction Description $ Amount")
    end_index = text.find("Total fees charged in")

    if start_index == -1 or end_index == -1:
        st.error("Could not find the expected transaction section in the PDF.")
    else:
        transaction_text = text[start_index:end_index].replace(
            "Transaction Merchant  Name or Transaction Description $ Amount", " "
        )

        # Parse each valid line
        valid_lines = []
        for line in transaction_text.split("\n"):
            if re.match(r"^\d{2}/\d{2}", line):
                valid_lines.append(line)

        # Build dataframe
        columns = ["Transaction Date", "Description", "Amount"]
        df = pd.DataFrame(columns=columns)

        new_line = {}
        current_text = ""

        for line in valid_lines:
            for item in line.split(" "):
                date_pattern = r"\d{2}/\d{2}"
                if re.match(date_pattern, item):
                    new_line["Transaction Date"] = item

                elif "." in item:
                    try:
                        float(item)
                        new_line["Amount"] = item
                        new_line["Description"] = current_text.strip()
                        current_text = ""
                        df = pd.concat([df, pd.DataFrame([new_line])], ignore_index=True)
                        new_line = {}

                    except:
                        current_text += " " + item
                else:
                    current_text += " " + item

        st.dataframe(df)

        # Offer CSV download
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{local_file.name.replace('.pdf', '')}.csv",
            mime="text/csv"
        )
