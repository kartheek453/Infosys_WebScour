import os
import json
import string
from flask import Flask, render_template, request

app = Flask(__name__)

# ---------- PATH SETUP ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INDEX_PATH = os.path.join(BASE_DIR, "..", "inverted_index.json")
IDF_PATH = os.path.join(BASE_DIR, "..", "idf.json")

# ---------- LOAD INDEX DATA ----------
with open(INDEX_PATH, "r", encoding="utf-8") as f:
    inverted_index = json.load(f)

with open(IDF_PATH, "r", encoding="utf-8") as f:
    idf = json.load(f)

# ---------- TOKENIZER ----------
def tokenize(text):
    text = text.lower()
    translator = str.maketrans("", "", string.punctuation)
    text = text.translate(translator)
    return text.split()

# ---------- SEARCH FUNCTION ----------
def search(query, top_k=5):
    scores = {}
    tokens = tokenize(query)

    for word in tokens:
        if word not in inverted_index:
            continue

        for doc_id, tf in inverted_index[word]:
            score = tf * idf.get(word, 0)
            scores[doc_id] = scores.get(doc_id, 0) + score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

# ---------- ROUTE ----------
@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query")
        results = search(query)

    return render_template("index.html", query=query, results=results)

# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(debug=True)
