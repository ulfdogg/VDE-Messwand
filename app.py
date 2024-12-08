from flask import Flask, render_template, request, redirect, url_for, flash

import random

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For flash messages

# Subfunctions
def subfunction_1_1(): return "Function 1-1: Output 101"
def subfunction_1_2(): return "Function 1-2: Output 102"
def subfunction_1_3(): return "Function 1-3: Output 103"
def subfunction_1_4(): return "Function 1-4: Output 104"
def subfunction_1_5(): return "Function 1-5: Output 105"

def subfunction_2_1(): return "Function 2-1: Output 201"
def subfunction_2_2(): return "Function 2-2: Output 202"
def subfunction_2_3(): return "Function 2-3: Output 203"
def subfunction_2_4(): return "Function 2-4: Output 204"
def subfunction_2_5(): return "Function 2-5: Output 205"

def subfunction_3_1(): return "Function 3-1: Output 301"
def subfunction_3_2(): return "Function 3-2: Output 302"
def subfunction_3_3(): return "Function 3-3: Output 303"
def subfunction_3_4(): return "Function 3-4: Output 304"
def subfunction_3_5(): return "Function 3-5: Output 305"

# Main functions
def function_1():
    subfunctions = [subfunction_1_1, subfunction_1_2, subfunction_1_3, subfunction_1_4, subfunction_1_5]
    return random.choice(subfunctions)()

def function_2():
    subfunctions = [subfunction_2_1, subfunction_2_2, subfunction_2_3, subfunction_2_4, subfunction_2_5]
    return random.choice(subfunctions)()

def function_3():
    subfunctions = [subfunction_3_1, subfunction_3_2, subfunction_3_3, subfunction_3_4, subfunction_3_5]
    return random.choice(subfunctions)()

main_functions = [function_1, function_2, function_3] * 7

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/measurement', methods=['POST'])
def measurement():
    return render_template('measurement.html')

@app.route('/solutions', methods=['POST'])
def solutions():
    code = request.form.get('code')
    if code == "1234":
        selected_functions = random.sample(main_functions, 3)
        results = [func() for func in selected_functions]
        return render_template('solutions.html', results=results)
    else:
        flash("Incorrect code! Access denied.")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
