from flask import Flask, render_template, request, redirect, url_for, session, flash # type: ignore
import mysql.connector # type: ignore
from functools import wraps
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = b'W9\xb9\x87\xb1>f\xa7\xf4\xbe\xe3\xcfD][\xfeK\xdef\xed\x01u\xd6\xa9'  # Chave secreta gerada

# Configuração do banco de dados
db_config = {
    'user': 'root',
    'password': 'dell123',
    'host': 'localhost',
    'database': 'controle_vendas'
}

# Decorator para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Você precisa estar logado para acessar esta página.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para verificar se o usuário é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Apenas administradores podem acessar esta página.", "error")
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def inicio():
    return render_template('inicio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            if user:
                session['logged_in'] = True
                session['username'] = username
                session['role'] = user['role']
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('inicio'))
            else:
                flash("Usuário ou senha incorretos.", "error")
        except mysql.connector.Error as err:
            flash(f"Erro no banco de dados: {err}", "error")
        finally:
            cursor.close()
            conn.close()
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    flash("Você foi desconectado.", "info")
    return redirect(url_for('login'))

@app.route('/novocliente', methods=['GET', 'POST'])
@login_required
def novocliente():
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = request.form['tipo']
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clientes (nome, tipo) VALUES (%s, %s)", (nome, tipo))
            conn.commit()
            flash("Cliente adicionado com sucesso!", "success")
        except mysql.connector.Error as err:
            flash(f"Erro ao adicionar cliente: {err}", "error")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('clientes'))
    return render_template('novocliente.html')

@app.route('/novavenda', methods=['GET', 'POST'])
@login_required
def novavenda():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        cursor.execute("SELECT * FROM estoque")
        estoque = cursor.fetchall()

        if request.method == 'POST':
            cliente_id = request.form['cliente_id']
            item_id = request.form['item_id']
            quantidade = int(request.form['quantidade'])
            data_venda = request.form['data_venda']
            valor = float(request.form['valor'])
            
            # Atualizar a quantidade no estoque
            cursor.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s", (quantidade, item_id))
            
            # Inserir a nova venda
            cursor.execute("INSERT INTO vendas (cliente_id, item_id, quantidade, data_venda, valor) VALUES (%s, %s, %s, %s, %s)", (cliente_id, item_id, quantidade, data_venda, valor))
            
            conn.commit()
            flash("Venda registrada com sucesso!", "success")
            return redirect(url_for('relatorios'))
    except mysql.connector.Error as err:
        flash(f"Erro ao registrar venda: {err}", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return render_template('novavenda.html', clientes=clientes, estoque=estoque)

@app.route('/usuarios')
@login_required
@admin_required
def usuarios():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        return render_template('usuarios.html', usuarios=usuarios)
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar usuários: {err}", "error")
        return redirect(url_for('inicio'))
    finally:
        cursor.close()
        conn.close()

@app.route('/novousuario', methods=['GET', 'POST'])
@login_required
@admin_required
def novousuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
            conn.commit()
            flash("Usuário adicionado com sucesso!", "success")
        except mysql.connector.Error as err:
            flash(f"Erro ao adicionar usuário: {err}", "error")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('usuarios'))
    return render_template('novousuario.html')

@app.route('/editarusuario/<int:id>', methods=['POST'])
@login_required
@admin_required
def editarusuario(id):
    role = request.form['role']
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET role = %s WHERE id = %s", (role, id))
        conn.commit()
        flash("Usuário atualizado com sucesso!", "success")
    except mysql.connector.Error as err:
        flash(f"Erro ao atualizar usuário: {err}", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('usuarios'))

@app.route('/editarcliente/<int:id>', methods=['POST'])
@login_required
@admin_required
def editarcliente(id):
    nome = request.form['nome']
    tipo = request.form['tipo']
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE clientes SET nome = %s, tipo = %s WHERE id = %s", (nome, tipo, id))
        conn.commit()
        flash("Cliente atualizado com sucesso!", "success")
    except mysql.connector.Error as err:
        flash(f"Erro ao atualizar cliente: {err}", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('relatorios'))

@app.route('/editarvenda/<int:id>', methods=['POST'])
@login_required
@admin_required
def editarvenda(id):
    data_venda = request.form['data_venda']
    valor = request.form['valor']
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE vendas SET data_venda = %s, valor = %s WHERE id = %s", (data_venda, valor, id))
        conn.commit()
        flash("Venda atualizada com sucesso!", "success")
    except mysql.connector.Error as err:
        flash(f"Erro ao atualizar venda: {err}", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('relatorios'))

@app.route('/estoque')
@login_required
def estoque():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM estoque")
        estoque = cursor.fetchall()
        return render_template('estoque.html', estoque=estoque)
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar estoque: {err}", "error")
        return redirect(url_for('inicio'))
    finally:
        cursor.close()
        conn.close()

@app.route('/novoitem', methods=['GET', 'POST'])
@login_required
def novoitem():
    if request.method == 'POST':
        produto = request.form['produto']
        quantidade = int(request.form['quantidade'])
        preco_compra = float(request.form['preco_compra'])
        preco_venda_vip1 = float(request.form['preco_venda_vip1'])
        preco_venda_vip2 = float(request.form['preco_venda_vip2'])
        preco_venda_comum = float(request.form['preco_venda_comum'])
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT id, quantidade FROM estoque WHERE produto = %s", (produto,))
            item = cursor.fetchone()
            if item:
                novo_estoque = item[1] + quantidade
                cursor.execute("UPDATE estoque SET quantidade = %s, preco_compra = %s, preco_venda_vip1 = %s, preco_venda_vip2 = %s, preco_venda_comum = %s WHERE id = %s", 
                               (novo_estoque, preco_compra, preco_venda_vip1, preco_venda_vip2, preco_venda_comum, item[0]))
            else:
                cursor.execute("INSERT INTO estoque (produto, quantidade, preco_compra, preco_venda_vip1, preco_venda_vip2, preco_venda_comum) VALUES (%s, %s, %s, %s, %s, %s)", 
                               (produto, quantidade, preco_compra, preco_venda_vip1, preco_venda_vip2, preco_venda_comum))
            conn.commit()
            flash("Item adicionado com sucesso!", "success")
        except mysql.connector.Error as err:
            flash(f"Erro ao adicionar item: {err}", "error")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('estoque'))
    return render_template('novoitem.html')

@app.route('/editaritem/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editaritem(id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        if request.method == 'POST':
            produto = request.form['produto']
            quantidade = int(request.form['quantidade'])
            preco_compra = float(request.form['preco_compra'])
            preco_venda_vip1 = float(request.form['preco_venda_vip1'])
            preco_venda_vip2 = float(request.form['preco_venda_vip2'])
            preco_venda_comum = float(request.form['preco_venda_comum'])
            cursor.execute("""
                UPDATE estoque 
                SET produto = %s, quantidade = %s, preco_compra = %s, preco_venda_vip1 = %s, preco_venda_vip2 = %s, preco_venda_comum = %s 
                WHERE id = %s
            """, (produto, quantidade, preco_compra, preco_venda_vip1, preco_venda_vip2, preco_venda_comum, id))
            conn.commit()
            flash("Item atualizado com sucesso!", "success")
            return redirect(url_for('estoque'))
        cursor.execute("SELECT * FROM estoque WHERE id = %s", (id,))
        item = cursor.fetchone()
        return render_template('editaritem.html', item=item)
    except mysql.connector.Error as err:
        flash(f"Erro ao editar item: {err}", "error")
        return redirect(url_for('estoque'))
    finally:
        cursor.close()
        conn.close()

@app.route('/excluiritem/<int:id>', methods=['POST'])
@login_required
@admin_required
def excluiritem(id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estoque WHERE id = %s", (id,))
        conn.commit()
        flash("Item excluído com sucesso!", "success")
    except mysql.connector.Error as err:
        flash(f"Erro ao excluir item: {err}", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('estoque'))

@app.route('/ajuda')
@login_required
def ajuda():
    return render_template('ajuda.html')

@app.route('/sair')
@login_required
def sair():
    session.clear()
    flash("Você foi desconectado.", "info")
    return redirect(url_for('login'))

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

@app.route('/alterar_senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']
        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('alterar_senha'))
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT password FROM usuarios WHERE username = %s", (session['username'],))
            usuario = cursor.fetchone()
            if usuario and usuario['password'] == senha_atual:
                cursor.execute("UPDATE usuarios SET password = %s WHERE username = %s", (nova_senha, session['username']))
                conn.commit()
                flash("Senha alterada com sucesso!", "success")
                return redirect(url_for('inicio'))
            else:
                flash("Senha atual incorreta.", "error")
        except mysql.connector.Error as err:
            flash(f"Erro ao alterar senha: {err}", "error")
        finally:
            cursor.close()
            conn.close()
    return render_template('alterar_senha.html')

def obter_lista_de_clientes():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        return clientes
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar clientes: {err}", "error")
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/clientes')
def clientes():
    clientes = obter_lista_de_clientes()
    return render_template('clientes.html', clientes=clientes)

@app.route('/excluircliente/<int:id>', methods=['POST'])
@login_required
@admin_required
def excluircliente(id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
        conn.commit()
        flash("Cliente excluído com sucesso!", "success")
    except mysql.connector.Error as err:
        flash(f"Erro ao excluir cliente: {err}", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('clientes'))

def obter_vendas_por_mes():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT MONTH(data_venda) AS mes, SUM(valor) AS total
            FROM vendas
            WHERE YEAR(data_venda) = YEAR(CURDATE())
            GROUP BY MONTH(data_venda)
            ORDER BY mes;
        """)
        resultados = cursor.fetchall()
        vendas_por_mes = [0] * 12
        for resultado in resultados:
            mes = resultado['mes'] - 1
            vendas_por_mes[mes] = float(resultado['total'])
        return vendas_por_mes
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar vendas por mês: {err}", "error")
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/relatorios')
@login_required
def relatorios():
    return render_template('relatorios.html')

@app.route('/relatorios/clientes')
@login_required
def relatorio_clientes():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM clientes')
        clientes = cursor.fetchall()
        return render_template('relatorio_clientes.html', clientes=clientes)
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar relatório de clientes: {err}", "error")
        return redirect(url_for('relatorios'))
    finally:
        cursor.close()
        conn.close()

@app.route('/relatorios/vendas')
@login_required
def relatorio_vendas():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT vendas.id, clientes.nome AS cliente_nome, vendas.data_venda, vendas.valor
            FROM vendas
            JOIN clientes ON vendas.cliente_id = clientes.id;
        """)
        vendas = cursor.fetchall()
        return render_template('relatorio_vendas.html', vendas=vendas)
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar relatório de vendas: {err}", "error")
        return redirect(url_for('relatorios'))
    finally:
        cursor.close()
        conn.close()

@app.route('/relatorios/vendas-mes')
@login_required
def relatorio_vendas_mes():
    vendas_por_mes = obter_vendas_por_mes()
    return render_template('relatorio_vendas_mes.html', vendas_por_mes=vendas_por_mes)

def obter_tipos_clientes():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT tipo, COUNT(*) AS total FROM clientes GROUP BY tipo")
        resultados = cursor.fetchall()
        tipos_clientes = {'VIP1': 0, 'VIP2': 0, 'COMUM': 0}
        for resultado in resultados:
            tipos_clientes[resultado['tipo']] = resultado['total']
        return tipos_clientes
    except mysql.connector.Error as err:
        flash(f"Erro ao carregar tipos de clientes: {err}", "error")
        return {'VIP1': 0, 'VIP2': 0, 'COMUM': 0}
    finally:
        cursor.close()
        conn.close()

@app.route('/relatorios/tipos-clientes')
@login_required
def relatorio_tipos_clientes():
    tipos_clientes = obter_tipos_clientes()
    return render_template('relatorio_tipos_clientes.html', tipos_clientes=tipos_clientes)

if __name__ == '__main__':
    app.run(debug=True)