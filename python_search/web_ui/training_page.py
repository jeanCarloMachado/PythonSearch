import streamlit as st


def load_training_page():
    st.write("## Training Dataset")

    df = load_dataset()
    pdf = df.toPandas()
    st.dataframe(pdf)

    st.write("### Pandas describe")
    st.write(pdf.describe())
    import matplotlib.pyplot as plt

    st.write("### Label histogram")
    fig, ax = plt.subplots()
    ax.hist(pdf["label"], bins=20)
    st.pyplot(fig)


def load_dataset():
    from python_search.next_item_predictor.training_dataset import TrainingDataset

    df = TrainingDataset().build(use_cache=True)
    return df
