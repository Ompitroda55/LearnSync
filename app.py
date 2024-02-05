from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def flashCardApp():
    categories = ["Literature", "Mathematics", "Science", "History", "Geography", "Computer Science", "Art", "Music", "Health", "Business", "Test Preparation", "Miscellaneous"]
    return render_template('flash_cards.html', categories=categories)

if __name__ == '__main__':
    app.run()
