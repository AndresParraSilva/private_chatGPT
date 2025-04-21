import streamlit as st

from helpers import *


state = st.session_state

models = [
    "dall-e-3",
    "dall-e-2",
]
sizes = [
    "1024x1024",
    "1024x1792",
    "1792x1024",
]
qualities = [
    "standard",
    "hd",
]
if "model_index" not in state:
    state.model_index = 0
    state.n = 1
    state.size_index = 0
    state.quality_index = 0
    state.original_image = ""
    state.mask = ""
    state.prompt = ""
    state.edit_prompt = ""
    state.response = ""

st.header("Image generation")


def update_model_index():
    state.model_index = models.index(state.model)
    st.sidebar.write(f"changed to {state.model_index}")
st.sidebar.radio("Model", models, index=state.model_index, on_change=update_model_index, key="model")

def update_size_index():
    state.size_index = sizes.index(state.size)
    st.sidebar.write(f"changed to {state.size_index}")
st.sidebar.radio("Size (width by height)", sizes, index=state.size_index, on_change=update_size_index, key="size")

def update_quality_index():
    state.quality_index = qualities.index(state.quality)
    st.sidebar.write(f"changed to {state.quality_index}")
st.sidebar.radio("Quality", qualities, index=state.quality_index, on_change=update_quality_index, key="quality")

state.n = st.sidebar.slider("n", min_value=1, value=state.n, max_value=10, step=1, key="n_slider")

def change_image():
    state.original_image = state.image_uploader
st.file_uploader("Image to work with", type=["png", "jpg", "jpeg"], on_change=change_image, key="image_uploader")

if state.original_image:
    st.image(state.original_image)

if st.button("Variation"):
    if not state.original_image:
        st.error("Empty image")
    else:
        st.write(f"Getting image variation with parameters model={models[state.model_index]}, size={sizes[state.size_index]}, n={state.n}")
        client = get_client()
        state.response = client.images.create_variation(
            model=models[state.model_index],  # "dall-e-2",
            image=state.original_image,
            n=state.n,  # 1,
            size=sizes[state.size_index],  # "1024x1024"
        )

def change_mask():
    state.mask = state.mask_uploader
st.file_uploader("Mask to work with", type=["png", "jpg", "jpeg"], on_change=change_mask, key="mask_uploader")

if state.mask:
    st.image(state.mask)

def change_edit_prompt():
    state.edit_prompt = state.edit_prompt_input
st.text_input("Image edit prompt", on_change=change_edit_prompt, key="edit_prompt_input")

if st.button("Edit"):
    if not state.original_image:
        st.error("Empty image")
    elif not state.mask:
        st.error("Empty mask")
    elif not state.edit_prompt:
        st.write("Empty edit prompt")
    else:
        st.write(f"Getting edited image with parameters model={models[state.model_index]}, size={sizes[state.size_index]},n={state.n}, edit_prompt={state.edit_prompt}")
        client = get_client()
        state.response = client.images.edit(
            model=models[state.model_index],  # "dall-e-2",
            image=state.original_image,
            mask=state.mask,
            prompt=state.edit_prompt,
            n=state.n,
            size=sizes[state.size_index],  # "1024x1024"
        )

def change_prompt():
    state.prompt = state.prompt_input
st.chat_input("Image creation prompt", on_submit=change_prompt, key="prompt_input")

if state.prompt:
    st.write(f"Getting image with parameters model={models[state.model_index]}, size={sizes[state.size_index]}, quality={qualities[state.quality_index]}, n={state.n}")
    client = get_client()
    state.response = client.images.generate(
        model=models[state.model_index],
        prompt=state.prompt,
        size=sizes[state.size_index],
        quality=qualities[state.quality_index],
        n=state.n,
    )
    state.prompt = ""

if state.response:
    for d in state.response.data:
       st.write(d.url)
       st.image(d.url)

# baroque tarot card the hanged man upside down hanging from one leg, the other leg tucked, with a crow on the side very baroque style
# baroque tarot card the hanged man upside down, suffering expression, hanging from one leg, the other leg tucked, with a crow on the side very baroque style
# baroque tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, with a crow on the side very baroque style, sepia tones
# detailed tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, with a crow on the side very baroque style, sepia tones
# detailed full tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, with a crow on the side very baroque style, sepia tones
# detailed full tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, in the woods, with a crow on the side very baroque style, sepia and green tones. Include card borders.
# detailed full tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, in the woods, with a crow on the side very baroque style, sepia and green tones. Include card borders up and down.
# detailed full tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, in the woods, with a crow on the side very baroque style, sepia and green tones. Include card borders up and down and the card legend "THE HANGED MAN".
# detailed full tarot card the hanged man upside down, super-crazy face expression, hanging from one leg, the other leg tucked, from a distance, with a crow on the side very baroque style, sepia and green tones. Include card borders up and down and the card legend "THE HANGED MAN".
# detailed full tarot card the hanged man upside down, super-crazy face expression, hanging from a tree by one leg, the other leg tucked, from a distance, with a crow on the side very baroque style, sepia and green tones. Include card borders up and down and the card legend "THE HANGED MAN".
# detailed full tarot card the hanged man, super-crazy face expression, hanging upside down from a tree by one leg, the other leg tucked, from a distance, with a crow on the side very baroque style, sepia and green tones. Include card borders up and down and the card legend "THE HANGED MAN".