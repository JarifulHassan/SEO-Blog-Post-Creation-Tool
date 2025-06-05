import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import random

GEMINI_API_KEY = "AIzaSyB0m8pptohxxcrgyyuhO1kDgOXzQKlvxam1kqOmTec"  # Your API key here

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

def scrape_ebay_product(search_query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    items = soup.select(".s-item")
    valid_products = []

    for item in items[:20]:
        title_tag = item.select_one(".s-item__title") or item.select_one("h3")
        price_tag = item.select_one(".s-item__price")
        img_tag = item.select_one("img.s-item__image-img") or item.find("img")
        link_tag = item.select_one("a.s-item__link")

        title = title_tag.text.strip() if title_tag else None
        price = price_tag.get_text(strip=True) if price_tag else None
        image = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
        link = link_tag.get("href") if link_tag else None

        if price and " to " in price:
            price = price.split(" to ")[0]

        if image and 's-l64' in image:
            image = image.replace('s-l64', 's-l500')

        if all([title, price, link, image]):
            valid_products.append({
                "title": title,
                "price": price,
                "image": image,
                "link": link
            })

    if not valid_products:
        return None
    return random.choice(valid_products)

def generate_blog(product):
    prompt = f"""
Write a 150-200 word SEO-friendly blog post for this product:

Title: {product['title']}
Price: {product['price']}
Link: {product['link']}

Make it engaging, include persuasive language, and end with a call-to-action.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def main():
    st.title("🛍️ eBay Product Blog Generator with Gemini AI")

    search_query = st.text_input("Enter product search query", value="bluetooth speaker")

    if st.button("Generate Blog"):
        with st.spinner("🔍 Scraping eBay..."):
            product = scrape_ebay_product(search_query)

        if product is None:
            st.error("❌ No valid products found on eBay for that query.")
            return

        st.success(f"✅ Selected Product: {product['title']}")
        st.image(product['image'], width=250)
        st.markdown(f"**Price:** {product['price']}")
        st.markdown(f"[🔗 Click here to view the product]({product['link']})")



        with st.spinner("📝 Generating blog post..."):
            blog_text = generate_blog(product)

        st.subheader("Generated Blog Post:")
        st.write(blog_text)

        safe_title = product['title'].split()[0].replace('/', '_')
        filename = f"blog_{safe_title}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(blog_text)

        with open(filename, "rb") as f:
            st.download_button(
                label="📥 Download Blog as Text File",
                data=f,
                file_name=filename,
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
