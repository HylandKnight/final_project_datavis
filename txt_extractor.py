from ebooklib import epub
from bs4 import BeautifulSoup

def epub_to_txt(epub_path, txt_path):
    book = epub.read_epub(epub_path)
    text = []
    for object in book.get_items():
        if isinstance(object, epub.EpubHtml):
            soup = BeautifulSoup(object.get_content(), 'lxml') # could also use html.parser
            paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
            cleaned_text = '\n\n'.join(paragraphs)
            text.append(cleaned_text + '\n\n')
    with open(txt_path, 'w') as output:
        output.write('\n\n'.join(text))
    print(f'Text successfully extracted to {txt_path}')

epub_to_txt('the_best_minds_of_my_generation.epub', 'best_minds.txt')