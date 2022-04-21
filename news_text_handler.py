from docx import Document


def text_handler(doc):
    document = Document(doc)
    data = document.paragraphs
    output = []
    headers = []
    for elem in data:
        print(elem.text)
        header_t = ''
        for run in elem.runs:
            if run.bold:
                header_t += run.text
        if header_t != '':
            headers.append(''.join(header_t))
    for elem in data:
        if elem.text in headers:
            output.append(f'<h3>{elem.text}</h3>')
        else:
            output.append(f'<p class="new-text">{elem.text}</p>')
    print('\n'.join(output))


text_handler('example.docx')