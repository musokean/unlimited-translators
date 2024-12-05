from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import concurrent.futures

app = FastAPI()

# Translate large text blocks
def translate_large_text(text, source_lang="en", target_lang="es", max_length=5000):
    def split_text(text, max_length):
        chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
        return chunks

    chunks = split_text(text, max_length)
    def translate_chunk(chunk):
        try:
            return GoogleTranslator(source=source_lang, target=target_lang).translate(chunk)
        except Exception as e:
            print(f"Translation failed. Error: {e}")
            return ""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        translated_chunks = list(executor.map(translate_chunk, chunks))
    return ''.join(translated_chunks)

# Translate HTML content and preserve structure
def translate_html(html_content, source_lang="en", target_lang="es"):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    def translate_element(element):
        if element.parent.name not in ['style', 'script']:  # Skip non-textual elements
            original_text = element.strip()
            if original_text:
                try:
                    translated_text = translate_large_text(original_text, source_lang, target_lang)
                    element.replace_with(translated_text)
                except Exception as e:
                    print(f"Translation failed for text: {original_text}. Error: {e}")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(translate_element, soup.find_all(string=True))
    
    return str(soup)

# FastAPI endpoint for translation
@app.post("/translate/", response_class=HTMLResponse)
async def translate_endpoint(html_content: str = Form(...), source_lang: str = Form("en"), target_lang: str = Form("es")):
    try:
        translated_html = translate_html(html_content, source_lang, target_lang)
        return translated_html
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files for HTML content
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory=".", html=True), name="static")
