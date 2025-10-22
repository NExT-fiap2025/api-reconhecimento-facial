# O código CORRETO para web_frontend.py

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # A rota RAIZ deve servir a página de LOGIN
    return render_template('index.html') 

@app.route('/admin')
def admin_page():
    # A rota ADMIN deve servir o PAINEL ADMIN
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)