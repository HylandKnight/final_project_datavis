import spacy
import networkx as nx
from itertools import combinations
from collections import Counter
import dash
import dash_cytoscape as cyto
from dash import html
from dash.dependencies import Input, Output

# Using NER to identify writers
nlp = spacy.load('en_core_web_sm') # a pretrained NLP model

combined_names = {
    'Jack': 'Jack Kerouac',
    'Kerouac': 'Jack Kerouac',
    'Ginsberg': 'Allen Ginsberg',
    'Allen': 'Allen Ginsberg',
    'Williams': 'William Carlos Williams',
    'Neal': 'Neal Cassady',
    'Cassady': 'Neal Cassady',
    'Carl': 'Carl Solomon',
    'Solomon': 'Carl Solomon',
    'Corso': 'Gregory Corso',
    'Gregory': 'Gregory Corso',
    'Holmes': 'John Clellon Holmes',
    'Huncke': 'Herbert Huncke',
    'Herbert': 'Herbert Huncke',
    'Bill': 'William S. Burroughs',
    'William Burroughs': 'William S. Burroughs',
    'Burroughs': 'William S. Burroughs',
    'Lucien': 'Lucien Carr',
    'Carr': 'Lucien Carr',
    'Joan': 'Joan Burroughs',
    'Peter': 'Peter Orlovsky',
    'Orlovsky': 'Peter Orlovsky',
    'Melville': 'Herman Melville',
    'Snyder': 'Gary Snyder',
    'Wolfe': 'Thomas Wolfe',
    'Rimbaud': 'Arthur Rimbaud',
    'Shakespeare': 'William Shakespeare',
    'Dostoyevsky': 'Fyodor Dostoevsky',
    'Eliot': 'T. S. Eliot',
    'Whitman': 'Walt Whitman',
    'Spengler': 'Oswald Spengler',
    'Hemingway': 'Ernest Hemingway',
    'Yeats': 'William Butler Yeats',    
}

excluded_names = {
    'Cody', 'Dean', 'Junkie', 'Beat', 'Joe', 'Sax', 'Arnold', 'Benway', 'Francis', 'Johnson', 'Paterson', 'Israel Hans', 'Levinsky', 'Claude', 'Johnnie', 'Norton', 'Lee', 'Sweet Levinsky', 'Mindfield', "Corso's", 'Angel Midnight', 'Titman'
    }

def extract_names(filepath, start_line=0):  
    with open(filepath, 'r') as input:
        text = ''.join(input.readlines()[start_line:]) # this allows us to skip copywright and table of contents in the plain text
    processed = nlp(text)
    people = [ent.text for ent in processed.ents if ent.label_ == 'PERSON']
    standardized_people = [combined_names.get(person, person) for person in people]
    filtered_people = [name for name in standardized_people if name not in excluded_names]
    
    return Counter(filtered_people)


name_counts = extract_names('best_minds.txt', start_line=252)
top_names = [name for name, _ in name_counts.most_common(27)]


# Identifying sentence level co-occurance
def co_occurrences_sentence(filepath, name_list, start_line=0):
    with open(filepath, 'r') as input:
        text = ''.join(input.readlines()[start_line:])
    processed = nlp(text)
    sentences = [sent.text.strip() for sent in processed.sents]
    cooccurrence_counts = Counter()
    for sentence in sentences:
        sent_processed = nlp(sentence)
        found_names = {ent.text for ent in sent_processed.ents if ent.label_ == 'PERSON' and ent.text in name_list}
        for pair in combinations(found_names, 2):
            cooccurrence_counts[pair] += 1 # if more than one name is found, creates all possible pairs
    G = nx.Graph()
    for (name1, name2), weight in cooccurrence_counts.items():
        G.add_edge(name1, name2, weight=weight)

    return G

#Identifying paragraph level co-occurance
def co_occurrences_paragraph(filepath, name_list, start_line=0):
    with open(filepath, 'r') as input:
        text = ''.join(input.readlines()[start_line:])
    paragraphs = text.split("\n\n")
    cooccurrence_counts = Counter()
    for paragraph in paragraphs:
        para_processed = nlp(paragraph)
        found_names = {ent.text for ent in para_processed.ents if ent.label_ == 'PERSON' and ent.text in name_list}
        for pair in combinations(found_names, 2):
            cooccurrence_counts[pair] += 1  # Count occurrences within the paragraph
    G = nx.Graph()
    for (name1, name2), weight in cooccurrence_counts.items():
        G.add_edge(name1, name2, weight=weight)

    return G

G_sentences = co_occurrences_sentence('best_minds.txt', top_names, start_line=252)
G_paragraphs = co_occurrences_paragraph('best_minds.txt', top_names, start_line=252)

#Vizualization
def nx_to_cytoscape(G):
    nodes = [{"data": {"id": node, "label": node}} for node in G.nodes()]
    edges = [{"data": {"source": edge[0], "target": edge[1], "weight": edge[2]['weight']}} for edge in G.edges(data=True)]
    return nodes, edges

nodes_sent, edges_sent = nx_to_cytoscape(G_sentences)
nodes_para, edges_para = nx_to_cytoscape(G_paragraphs)


non_beat_writers = {
    'William Shakespeare', 'Foydor Dostoevsky', 'T. S. Eliot', 'Walt Whitman', 'Oswald Spengler', 'Earnest Hemingway', 'William Butler Yeats', 'Arthur Rimbaud', 'Herman Melville', 'Thomas Wolfe', 'Charlie Parker', 'Ezra Pound'
}

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Network of Writers in Allen Ginsberg's 'The Best Minds of My Generation'", 
            style={'textAlign': 'center', 'padding': '10px'}),

    # sentence-level
    html.Div([
        html.H3("Sentence-Level Co-Occurrence", style={'textAlign': 'center'}),
        cyto.Cytoscape(
            id='cytoscape-sentence-network',
            elements=nodes_sent + edges_sent,
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '500px'},
            stylesheet=[
                # beat nodes
                {'selector': 'node', 'style': {
                    'content': 'data(label)',
                    'color': 'black',
                    'background-color': 'lightblue',
                    'width': '180px',  # allows me to fit all the names within the nodes themselves
                    'height': '50px',
                    'text-halign': 'center',
                    'text-valign': 'center',
                }},
                
                # non-beat nodes (red)
                *[
                    {'selector': f'[id = "{name}"]', 'style': {'background-color': '#ff9999'}}  # code for light red
                    for name in non_beat_writers
                ],

                # edge styling
                {'selector': 'edge', 'style': {
                    'line-color': 'gray',
                    'width': 'data(weight)', 
                }}
            ]
        )
    ], style={'margin-bottom': '30px'}),  # adds space between the graphs

    # paragraph-level
    html.Div([
        html.H3("Paragraph-Level Co-Occurrence Network", style={'textAlign': 'center'}),
        cyto.Cytoscape(
            id='cytoscape-paragraph-network',
            elements=nodes_para + edges_para,
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '500px'},
            stylesheet=[
                {'selector': 'node', 'style': {
                    'content': 'data(label)',
                    'color': 'black', 
                    'background-color': 'lightblue',
                    'width': '180px', 
                    'height': '50px',
                    'text-halign': 'center',
                    'text-valign': 'center',
                }},
                
                *[
                    {'selector': f'[id = "{name}"]', 'style': {'background-color': '#ff9999'}}
                    for name in non_beat_writers
                ],

                {'selector': 'edge', 'style': {
                    'line-color': 'gray',
                    'width': 'data(weight)', 
                }}
            ]
        )
    ]),

    # hover data output
    html.Div(id='hover-data', style={'padding': '10px', 'fontSize': '16px'}), 
    html.Div(id='edge-hover-data', style={'padding': '10px', 'fontSize': '16px', 'color': 'gray'})
])

@app.callback(
    [Output('hover-data', 'children'),
     Output('edge-hover-data', 'children')],
    [Input('cytoscape-sentence-network', 'mouseoverNodeData'),
     Input('cytoscape-sentence-network', 'mouseoverEdgeData'),
     Input('cytoscape-paragraph-network', 'mouseoverNodeData'),
     Input('cytoscape-paragraph-network', 'mouseoverEdgeData')]
)
def display_hover_info(node_sent, edge_sent, node_para, edge_para):
    # node hover
    node_info = "Hover over a node to see details."
    if node_sent:
        node_info = f"[Sentence Level] Name: {node_sent['label']}"
    elif node_para:
        node_info = f"[Paragraph Level] Name: {node_para['label']}"

    # edge hover
    edge_info = "Hover over an edge to see co-occurrence weight."
    if edge_sent:
        source, target = edge_sent['source'], edge_sent['target']
        weight = edge_sent.get('weight', 'N/A')
        edge_info = f"[Sentence Level] {source} ↔ {target} (Weight: {weight})"
    elif edge_para:
        source, target = edge_para['source'], edge_para['target']
        weight = edge_para.get('weight', 'N/A')
        edge_info = f"[Paragraph Level] {source} ↔ {target} (Weight: {weight})"

    return node_info, edge_info


if __name__ == '__main__':
    app.run_server(debug=True)