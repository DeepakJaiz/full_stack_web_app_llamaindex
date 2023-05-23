from flask import Flask, request, jsonify, make_response
import pickle
import os
from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex, StorageContext, ServiceContext
from multiprocessing import Lock
from werkzeug.utils import secure_filename
# NOTE: for local testing only, do NOT deploy with your key hardcoded
os.environ['OPENAI_API_KEY'] = "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"

index = None
stored_docs = {}
lock = Lock()


def initialize_index(query_text):
    global index
    storage_context = StorageContext.from_defaults()
    documents = SimpleDirectoryReader("./documents").load_data()
    index = GPTVectorStoreIndex.from_documents(documents, storage_context=storage_context)
    storage_context.persist()
    query_engine = index.as_query_engine()
    response = query_engine.query(query_text)
    return str(response)

def insert_into_index(doc_text, doc_id=None):
    global index
    document = SimpleDirectoryReader(input_files=[doc_text]).load_data()[0]
    if doc_id is not None:
        document.doc_id = doc_id


    with lock:
        index.insert(document)
        index.storage_context.persist()



from flask import request

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World!"

@app.route("/uploadFile", methods=["POST"])
def upload_file():
   
    if 'file' not in request.files:
         print(request.files)
         return "Please send a POST request with a file", 400

    filepath = None
    try:
        uploaded_file = request.files["file"]
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join('documents', filename)
        uploaded_file.save(filepath)

        # if request.form.get("filename_as_doc_id", None) is not None:
        #    insert_into_index(filepath,doc_id=filename)
        # else:
        #    insert_into_index(filepath)
    except Exception as e:
        # cleanup temp file
        # if filepath is not None and os.path.exists(filepath):
        #     os.remove(filepath)
        return "Error: {}".format(str(e)), 500

    # cleanup temp file
    # if filepath is not None and os.path.exists(filepath):
    #     os.remove(filepath)

    return "File inserted!", 200



@app.route("/query", methods=["GET"])
def query_index():
  global index
  query_text = request.args.get("text", None)
  if query_text is None:
    return "No text found, please include a ?text=blah parameter in the URL", 400
 
  response = initialize_index(query_text)
  return str(response), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5601)
