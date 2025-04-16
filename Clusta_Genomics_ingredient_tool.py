import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Clusta Genomics Product Ingredient Tool", layout="centered")
st.title("Clusta Genomics Product Ingredient Tool")

product_name = st.text_input("Enter product name (e.g., 'CeraVe Moisturizing Cream')", value="Nivea Soft")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def search_inci(product):
    query = "+".join(product.strip().split())
    return f"https://incidecoder.com/search?query={query}"

@st.cache_data(show_spinner=True)
def get_product_links(product):
    search_url = search_inci(product)
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = {}
    for a in soup.select("a[href^='/products/']"):
        name = a.get_text(strip=True)
        link = "https://incidecoder.com" + a["href"]
        if name and link:
            results[name] = link
    return results

def scrape_ingredients_raw(url):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Try multiple ingredient location strategies
    ingredients_text = None
    elements_to_try = [
        ('div', {"id": "ingredlist-short"}),
        ('div', {"class": "ingredlist"}),
        ('h2', {"string": lambda t: t and "ingredients" in t.lower()})
    ]
    
    for tag, attrs in elements_to_try:
        element = soup.find(tag, attrs)
        if element:
            if tag == 'h2':
                text_block = element.find_next("div", class_="cp-content__text")
                if text_block:
                    ingredients_text = text_block.get_text(" ", strip=True)
            else:
                ingredients_text = element.get_text(" ", strip=True)
            
            if ingredients_text:
                # Clean up formatting
                ingredients_text = ingredients_text.replace(" : ", ": ") \
                                                  .replace(" , ", ", ") \
                                                  .replace("[more]", "") \
                                                  .replace("[less]", "")
                ingredients_text = " ".join(ingredients_text.split())
                return ingredients_text.strip(' ,')
    
    return None

if product_name:
    with st.spinner("Searching for products..."):
        product_links = get_product_links(product_name)

    if product_links:
        selected_product = st.selectbox("Select a product to view ingredients:", list(product_links.keys()))

        if st.button("Scrape Ingredients"):
            with st.spinner("Scraping ingredients..."):
                raw_text = scrape_ingredients_raw(product_links[selected_product])
                if raw_text:
                    st.success("✅ Ingredients Successfully Extracted")
                    
                    # Display in clean paragraph format
                    st.subheader("Formatted Ingredients List")
                    st.write(raw_text)
                    
                    # Optional: Display in text area with line breaks
                    formatted_text = raw_text.replace(", ", ",\n")
                    st.text_area("Full Ingredients List", 
                               value=formatted_text, 
                               height=200,
                               disabled=True)
                else:
                    st.error("⚠️ No ingredients found. Possible reasons:\n"
                            "- Product page structure changed\n"
                            "- Ingredients not listed on source page\n"
                            "- Temporary website unavailability")
    else:
        st.warning("⚠️ No matching products found. Try adjusting your search terms.")