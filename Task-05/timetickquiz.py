
import html
import random
import requests
import sys
import time
import platform
import threading
import queue
import select

API_CATEGORY_URL = "https://opentdb.com/api_category.php"
API_QUESTIONS_URL = "https://opentdb.com/api.php"


def fetch_categories():
    try:
        r = requests.get(API_CATEGORY_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("trivia_categories", [])
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []


def choose_from_list(prompt, options, allow_any=True):
    print(prompt)
    if allow_any:
        print(" 0) Any")
    for i, item in enumerate(options, start=1 if allow_any else 0):
        print(f" {i}) {item}")
    while True:
        choice = input("Enter number: ").strip()
        if choice == "" and allow_any:
            return None
        if choice.isdigit():
            idx = int(choice)
            if allow_any and idx == 0:
                return None
            base = 1 if allow_any else 0
            if base <= idx <= base + len(options) - 1:
                return options[idx - base]
        print("Invalid choice — try again.")


def choose_category(categories):
    if not categories:
        return None
    names = [c["name"] for c in categories]
    sel = choose_from_list("Choose a category:", names, allow_any=True)
    if sel is None:
        return None
    for c in categories:
        if c["name"] == sel:
            return c["id"]
    return None


def choose_difficulty():
    opts = ["easy", "medium", "hard"]
    sel = choose_from_list("Choose difficulty:", opts, allow_any=True)
    return sel


def choose_type():
    opts = ["multiple", "boolean"]
    sel = choose_from_list("Choose type (multiple or boolean [True/False]):", opts, allow_any=True)
    return sel


def build_question_params(amount=10, category=None, difficulty=None, qtype=None):
    params = {"amount": amount}
    if category:
        params["category"] = category
    if difficulty:
        params["difficulty"] = difficulty
    if qtype:
        params["type"] = qtype
    return params


def fetch_questions(amount=10, category=None, difficulty=None, qtype=None):
    params = build_question_params(amount, category, difficulty, qtype)
    try:
        r = requests.get(API_QUESTIONS_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        code = data.get("response_code")
        if code != 0:
            print(f"OpenTDB returned response_code={code}. No questions found or invalid params.")
            return []
        return data.get("results", [])
    except Exception as e:
        print(f"Error fetching questions: {e}")
        return []


def timed_input(prompt, timeout):
    print(prompt, end="", flush=True)
    if platform.system() != "Windows":
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            line = sys.stdin.readline().rstrip("\n")
            return line, False
        else:
            return None, True
    else:
        q = queue.Queue()

        def inner():
            try:
                line = sys.stdin.readline().rstrip("\n")
                q.put(line)
            except Exception:
                q.put(None)

        t = threading.Thread(target=inner, daemon=True)
        t.start()
        try:
            answer = q.get(timeout=timeout)
            return answer, False
        except queue.Empty:
            return None, True


def ask_question(qdata, qnum, total, timeout_seconds=15):
    q_text = html.unescape(qdata.get("question", ""))
    correct = html.unescape(qdata.get("correct_answer", ""))
    incorrect = [html.unescape(a) for a in qdata.get("incorrect_answers", [])]
    qtype = qdata.get("type")

    if qtype == "boolean":
        options = ["True", "False"]
    else:
        options = incorrect + [correct]
        random.shuffle(options)

    print(f"\nQuestion {qnum}/{total} (you have {timeout_seconds} seconds):")
    print(q_text)

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i, opt in enumerate(options):
        print(f"  {letters[i]}) {opt}")

    start = time.time()
    answer, timed_out = timed_input("Your answer (letter or number): ", timeout_seconds)
    duration = time.time() - start

    if timed_out:
        print("\nTime's up!")
        print(f"Correct answer: {correct}")
        return False, True, correct

    ans = answer.strip()
    selected = None
    if ans == "":
        selected = None
    elif ans.isdigit():
        idx = int(ans) - 1
        if 0 <= idx < len(options):
            selected = options[idx]
    else:
        a = ans[0].upper()
        if a in letters[:len(options)]:
            idx = ord(a) - ord("A")
            selected = options[idx]

    if selected is None:
        print("Invalid answer format — counted as incorrect.")
        print(f"Correct answer: {correct}")
        return False, False, correct

    if selected == correct:
        print("Correct! (+1)")
        return True, False, correct
    else:
        print(f"Incorrect. You answered: {selected}")
        print(f"Correct answer: {correct}")
        return False, False, correct


def main():
    print("\n=== TimeTickQuiz — 15s per question ===\n")

    categories = fetch_categories()
    cat_id = choose_category(categories) if categories else None
    diff = choose_difficulty()
    qtype = choose_type()

    while True:
        amt = input("How many questions would you like (default 10)? ").strip()
        if amt == "":
            amt = 10
            break
        if amt.isdigit() and 1 <= int(amt) <= 50:
            amt = int(amt)
            break
        print("Enter a number between 1 and 50.")

    print("\nFetching questions...\n")
    questions = fetch_questions(amount=amt, category=cat_id, difficulty=diff, qtype=qtype)
    if not questions:
        print("No questions available with those filters. Try again later or choose other filters.")
        return

    score = 0
    total = len(questions)
    wrong_list = []

    for i, q in enumerate(questions, start=1):
        correct_flag, timed_out, correct_ans = ask_question(q, i, total, timeout_seconds=15)
        if correct_flag:
            score += 1
        else:
            wrong_list.append({
                "q": html.unescape(q.get("question", "")),
                "correct": correct_ans,
            })

    print("\n=== Game Over ===")
    print(f"Score: {score}/{total}")
    pct = (score / total) * 100 if total else 0
    print(f"Accuracy: {pct:.1f}%")

    if wrong_list:
        print("\nReview of missed questions:")
        for w in wrong_list:
            print(f" - {w['q']} — correct: {w['correct']}")

    print("\nThanks for playing TimeTickQuiz!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
