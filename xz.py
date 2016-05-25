import json
import random

def txt_to_json():
    f = open('questions.txt', 'r').read()
    id = 0
    q = f.split('===')
    questions = []
    for x in q:
        question = [m.strip() for m in x.split('---')]
        questions.append({
            'id': id,
            'question': question[0],
            'rus_question': question[1],
            'answer': question[2],
            'rus_answer': question[3],
        })
        id += 1

    print(json.dumps(questions))
    json.dump(questions, open('questions.json', 'w'), indent=2, ensure_ascii=False)

def add_answer_check():
    qs = json.load(open('questions.json', 'r'))
    for i, q in enumerate(qs):
        if 'answer_check' in q:
            continue
        print(json.dumps(q, indent=2, ensure_ascii=False))
        inp = input("answer_check=").strip().lower()
        if inp:
            qs[i]['answer_check'] = inp

    json.dump(qs, open('questions2.json', 'w'), indent=2, ensure_ascii=False)
"""
15 Bolesław I Chrobry

"""
add_answer_check()