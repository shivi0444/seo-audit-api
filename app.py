from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

app = Flask(__name__)
CORS(app)  # Enable CORS so frontend can communicate

def fetch_seo_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            return {"error": f"Status code: {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Title, Meta, H1
        title = soup.title.string.strip() if soup.title else "Missing"
        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_tag["content"].strip() if meta_tag and "content" in meta_tag.attrs else "Missing"
        h1_tag = soup.find("h1")
        h1 = h1_tag.get_text().strip() if h1_tag else "Missing"

        # Image alt check
        images = soup.find_all("img")
        total_images = len(images)
        missing_alt = sum(1 for img in images if not img.get("alt"))

        # Word count
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=' ')
        word_count = len(text.split())

        # Canonical tag
        canonical_tag = soup.find("link", rel="canonical")
        has_canonical = bool(canonical_tag and canonical_tag.get("href"))

        # robots.txt and sitemap.xml
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_check = requests.get(urljoin(base_url, "/robots.txt"), headers=headers)
        sitemap_check = requests.get(urljoin(base_url, "/sitemap.xml"), headers=headers)

        has_robots_txt = robots_check.status_code == 200
        has_sitemap_xml = sitemap_check.status_code == 200

        return {
            "title": title,
            "meta_description": meta_desc,
            "h1": h1,
            "total_images": total_images,
            "image_alt_missing": missing_alt,
            "word_count": word_count,
            "has_canonical": has_canonical,
            "has_robots_txt": has_robots_txt,
            "has_sitemap_xml": has_sitemap_xml
        }

    except Exception as e:
        return {"error": str(e)}

@app.route("/api/seo-audit", methods=["POST"])
def seo_audit():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400
    result = fetch_seo_data(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
