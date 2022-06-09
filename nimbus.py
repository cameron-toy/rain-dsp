import json
import numpy as np
import spacy
import sklearn.neighbors
from typing import Tuple
import re
import glob
import os
import joblib
import pickle
from datetime import datetime
from parse import Oracle
from db import Database
from entities.Club import ClubEnt
from entities.Professor import ProfessorEnt
from entities.Department import DepartmentEnt
from entities.Course import CourseEnt
from entities.Location import LocationEnt
from entities.Section import SectionEnt


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
now = datetime.now()
date_time = now.strftime("_%m_%d_%Y_%H_%M_%S")


def normalize_question_format(qformat):
    names = []
    matches = re.finditer(r'{(.+?)}', qformat, re.MULTILINE | re.DOTALL)
    vcounts = dict()

    for m in matches:
        captured = m.group(1)
        splitted = [c.strip() for c in captured.split(":")]
        match splitted:
            case [v, t]:
                names.append(v)
                qformat = qformat.replace(captured, t)
            case [v]:
                count = vcounts.setdefault(v, 0)
                vcounts[v] += 1
                names.append(f"{v}{count}")
            case _:
                raise ValueError() 

    return (qformat, names)


def check_char_boundary(s, i):
    return i <= 0 or i >= len(s) or not s[i].isalnum()

def count_replace(s, pat, rep, start=0):
    i = s.find(pat, start)
    replaces = 0
    indicies = []
    while i != -1:
        if check_char_boundary(s, i-1) and check_char_boundary(s, i+len(pat)):
            replaces += 1
            indicies.append(i)
            s = s[:i] + rep + s[i+len(pat):]
        i = s.find(pat, i+1)
    return (s, replaces, indicies)


def extract_variables(q, titles, model):
    q = q.lower()
    for title in titles:
        q = q.replace(title, "")
    
    # Remove double and end spaces
    q = re.sub(r' +', ' ', q.strip())

    start = 0
    names = []
    for (name, identifier, vartype) in model:
        (q, matches, indicies) = count_replace(q, name, "{" + vartype + "}", start=start)
        if matches != 0:
            start = indicies[-1]
            names.append(identifier)
    
    return (q, names)


def save_model(model, model_name):
    save_path = (
        PROJECT_DIR + "/models/classification/" + model_name + date_time + ".pkl"
    )
    f = open(save_path, "wb")
    pickle.dump(model, f)
    f.close()
    print("Saved model :", save_path)


def load_model(model_name):
    train_path = PROJECT_DIR + "/models/classification/" + model_name + ".joblib"
    return joblib.load(train_path)


def load_latest_model():
    # https://stackoverflow.com/a/39327156
    train_path = PROJECT_DIR + "/models/classification/*"
    list_of_files = glob.glob(train_path)
    latest_file = max(list_of_files, key=os.path.getctime)
    _, file_extension = os.path.splitext(latest_file)
    if file_extension != ".pkl":
        raise ValueError
    else:
        return joblib.load(latest_file)


TITLES = { "dr." }

class Nimbus:
    def __init__(self, model_path, oracle):
        with open(model_path, "r") as f:
            self.model = [line.split(", ") for line in f.read().splitlines() if len(line.split(", ")) == 3]

        # self.classifier = QuestionClassifier(qformats)
        self.oracle = oracle

    def answer(self, question):
        matched_qformat, extracted = extract_variables(question, TITLES, self.model)
        print("EXTRACTED:", extracted)
        # matched_qformat = self.classifier.classify_question(qformat)
        normalized_qformat, names = normalize_question_format(matched_qformat)
        print("NORMALIZED QFORMAT:", normalized_qformat)
        return self.oracle.answer(normalized_qformat, **dict(zip(names, extracted)))

    def repl(self):
        try:
            while True:
                q = input("> ")
                print(self.answer(q.strip()))
        except KeyboardInterrupt:
            return
                
class QuestionClassifier:
    def __init__(self, question_pairs=[], train=False):
        if train is True:
            self.classifier = self.build_question_classifier(question_pairs)
            save_model(self.classifier, "nlp-model")
        else:
            self.classifier = load_latest_model()

        with open(PROJECT_DIR + "/models/features/overall_features.json", "r") as fp:
            self.overall_features = json.load(fp)

        self.classifier = load_latest_model()
        self.nlp = spacy.load("en_core_web_sm")
        self.WH_WORDS = {"WDT", "WP", "WP$", "WRB"}
        self.overall_features = {}

    # Added question pairs as a parameter to remove database_wrapper as a dependency
    # Including database_wrapper introduces circular dependencies
    def build_question_classifier(self, question_pairs: Tuple[str, str]):
        """
        Build overall feature set for each question based on feature vectors of individual questions.
        Train KNN classification model with overall feature set.
        """
        questions = [q[0] for q in question_pairs]
        question_features = [
            self.get_question_features(self.nlp(str(normalize_question_format(q)))) for q in questions
        ]

        for feature in question_features:
            for key in feature:
                self.overall_features[key] = 0
        self.overall_features["not related"] = 0

        vectors = []
        for feature in question_features:
            vector_gen = [
                feature[k] if k in feature else 0 for k in self.overall_features
            ]
            vectors.append(np.array(vector_gen))

        vectors = np.array(vectors)
        y_train = np.array(questions)
        new_classifier = sklearn.neighbors.KNeighborsClassifier(n_neighbors=1)
        new_classifier.fit(vectors, y_train)

        with open(PROJECT_DIR + "/models/features/overall_features.json", "w") as fp:
            json.dump(self.overall_features, fp)

        return new_classifier

    def is_wh_word(self, token):
        return token.tag_ in self.WH_WORDS

    def filter_wh_tags(self, spacy_doc):
        return [t.text for t in spacy_doc if self.is_wh_word(t)]

    def validate_wh(self, s1, s2):
        # only parses as a spacy doc if necessary
        doc1 = s1 if type(s1) == spacy.tokens.doc.Doc else self.nlp(s1)
        doc2 = s2 if type(s2) == spacy.tokens.doc.Doc else self.nlp(s2)
        return self.filter_wh_tags(doc1) == self.filter_wh_tags(doc2)

    def get_question_features(self, spacy_doc):
        features = dict()

        for token in spacy_doc:

            # Filters stop words, punctuation, and symbols
            if token.is_stop or not (token.is_digit or token.is_alpha):
                continue

            # Add [VARIABLES] with weight 90.
            # token.i returns the index of the token, and token.nbor(n) return the token
            # n places away. Only the left neighbor is tested for brevity.
            elif token.i != 0 and token.nbor(-1).text == "[":
                features[token.text] = 90

            # Add WH words with weight 60
            # elif self.is_wh_word(token):
            # .lemma_ is already lowercase; no .lower() needed
            #    features[token.lemma_] = 3

            # Add all other words with weight 30
            else:
                features[token.lemma_] = 30

        # Replace the stemmed main verb with weight 60
        sent = next(spacy_doc.sents)
        stemmed_main_verb = sent.root.lemma_
        features[stemmed_main_verb] = 60

        return features

    def classify_question(self, question):
        if self.classifier is None:
            raise ValueError("Classifier is not initialized")

        # Create the spacy doc. Handles pos tagging, stop word removal, tokenization,
        # lemmatization, etc
        doc = self.nlp(question)
        test_features = self.get_question_features(doc)

        array_gen = [
            test_features[k] if k in test_features else 0 for k in self.overall_features
        ]
        test_array = np.array(array_gen)

        # Flatten array into a vector
        test_vector = test_array.reshape(1, -1)

        min_dist = np.min(self.classifier.kneighbors(test_vector, n_neighbors=1))

        if min_dist > 150:
            return "I don't recognize that question"

        # Cast to string because the classifier returns a numpy.str_, which causes issues
        # with the validate_wh function below.
        predicted_question = str(self.classifier.predict(test_vector)[0])
        # wh_words_match = self.validate_wh(doc, predicted_question)

        return predicted_question


if __name__=="__main__":
    DB_FILE = "calpoly.db"
    db = Database(
        databaseUrl=f"sqlite:///{DB_FILE}",
        entityConfig={
            ProfessorEnt: {
                "search_col": "alias",
                "name_remapping": "professors"
            },
            ClubEnt: {
                "search_col": "name",
                "name_remapping": "clubs",
            },
            DepartmentEnt: {
                "search_col": "name",
                "name_remapping": "departments"
            },
            LocationEnt: {
                "search_col": "id",
                "name_remapping": "locations"
            },
            CourseEnt: {
                "search_col": "title",
                "name_remapping": "courses"
            },
            SectionEnt: {
                "search_col": "title",
                "name_remapping": "sections"
            }
        }
    )
    oracle = Oracle(db)
    oracle.add_qa("What is {professor}'s email?", "`{professor0.name}'s email is {professor0.email}`")
    oracle.add_qa("What is {professor}'s phone number?", "`{professor0.name}'s phone number is {professor0.phone_number}`")
    oracle.add_qa("What type of course is {course}?", "`{course0.title} is a {course0.type}`")
    oracle.add_qa(
        "How many sections of {course} does {professor} teach?",
        "let secs = (professor0.teaches.filter (fn (sec) -> (eq? sec.course.name course0.name))) in "
        "(if (eq? (secs.length) 0)"
            "`{professor0.name} does not teach any sections of {course0.title}`"
            "`{professor0.name} teaches {(secs.length)} sections of {course0.title}`)"
    )
    oracle.add_qa(
        "What courses are {professor} teaching?",
        'let course_names = (professor0.teaches#course#name.dedup) in '
        '(if (course_names.empty)'
            '`{professor0.name} is not teaching any courses this quarter`'
            '`{professor0.name} is teaching {(course_names.grammatical_join "and")}`)'
    )
    what_sections = (
        'let prof_sections = (professor0.teaches.filter (fn (sec) -> (eq? sec.course.name course0.name))) in '
        '(if (prof_sections.empty)'
            '`{professor0.name} does not teach any sections of {course0.name}`'
            '`{professor0.name} teaches sections {(prof_sections#section_number.gjoin "and")} of {course0.name}`)'
    )
    oracle.add_qa("What sections of {course} does {professor} teach?", what_sections)
    oracle.add_qa("what sections of {course} is {professor} teaching?", what_sections)
    oracle.add_qa(
        "what is the earliest section of {course} taught by {professor}?",
        'let prof_sections = (professor0.teaches.filter (fn (sec) -> (eq? sec.course.name course0.name))) in '
        'let times = (prof_sections#start_time.map '
            '(fn (st) -> (+ (if (eq? (st.find "PM") -1) 0 12) (num (st.slice 0 (st.find ":")))))) in '
        'let earliest = (prof_sections.at (times.find (times.min))) in '
        '(if (times.empty)'
            '`{professor0.name} does not teach any sections of {course0.name}`'
            '`{professor0.name}\'s earliest section of {earliest.course.name} is {earliest.title} which starts at {earliest.start_time}`)'
    )
    oracle.add_qa(
        "What professors teach {course}?",
        'let profs_teaching = (course0.sections#instructor#name.dedup) in '
        '(if (profs_teaching.empty) '
            '`No professors are teaching {course0.title} this quarter`'
            '`{(profs_teaching.gjoin "and")} are teaching {course0.title} this quarter`)'
    )
    oracle.add_qa(
        "What course is taught by the most professors?",

        'let max_course = (courses.max_by (fn (course) -> (course.sections#instructor#name.dedup.length))) in '
        'let n_instructors = (max_course.sections#instructor#name.dedup.length) in '
        '`The course being taught by the most professors this quarter is {max_course.name} with {n_instructors} instructors.`'
    )
    nimbus = Nimbus("model.txt", oracle)
    nimbus.repl()
