#Import Libraries
from flask import Flask, render_template, request
import os
import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

# Docx resume
import docx2txt

#key words match
from nltk.tokenize import word_tokenize 
from nltk.corpus import stopwords
set(stopwords.words('english'))
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

#read PDF resume 
def read_pdf_resume(pdf_doc):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    
    with open(pdf_doc, 'rb') as fh:
        for page in PDFPage.get_pages(fh, 
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            
        text = fake_file_handle.getvalue()
    
    # close open handles
    converter.close()
    fake_file_handle.close()
    
    if text:
        return text
    
# Read word resume 
def read_word_resume(word_doc):
    resume = docx2txt.process(word_doc)
    resume = str(resume)
    
    text =  ''.join(resume)
    text = text.replace("\n", "")
    
    if text:
        return text

def extract_skills(text):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text)
    skills = [word.lower() for word in tokens if word.isalpha() and word.lower() not in stop_words]
    return set(skills)


# get jd and resume match score 
def get_resume_score(text):
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(text)
    #Print the similarity scores
    #print("\nSimilarity Scores:")
    #print(cosine_similarity(count_matrix))
    #get the match percentage
    matchPercentage = cosine_similarity(count_matrix)[0][1] * 100
    matchPercentage = round(matchPercentage, 2) # round to two decimal
    return matchPercentage


app = Flask(__name__,template_folder='templates')

# Define the route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Define the route for handling the resume and job description submission
@app.route('/scan', methods=['POST'])
def scan_resume():
    if request.method == 'POST':
        resume = request.files['resume']
        job_description = request.form['job_description']
        
        # Save the uploaded files temporarily
        resume_path = os.path.join('uploads', resume.filename)
        resume.save(resume_path)
        
        # Call your resume scanner functions
        if resume.filename.endswith('.pdf'):
            resume_text = read_pdf_resume(resume_path)
        else:
            resume_text = read_word_resume(resume_path)
        
        # Get job description keywords
        #clean_jd = clean_job_decsription(job_description)
        
        # Calculate match score
        text = [resume_text, job_description]
        match_percentage = get_resume_score(text)

        job_skills = extract_skills(job_description)
        resume_skills = extract_skills(resume_text)
        
        missing_skills = job_skills - resume_skills
        
        # Delete the temporary files
        os.remove(resume_path)
        
        return render_template('results.html', match_percentage=match_percentage, missing_skills=missing_skills)

if __name__ == '__main__':
    app.run(debug=True)
