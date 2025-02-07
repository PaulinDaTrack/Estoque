from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
import requests
import random
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='FrontEnd/templates', static_folder='FrontEnd/static')
app.secret_key = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

def conectar_banco():
    return mysql.connector.connect(
        host='srv1310.hstgr.io',
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        port=os.getenv('DB_PORT', '3306')
    )

def criar_tabela_usuarios():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(50) NOT NULL
        )
    ''')
    conexao.commit()
    cursor.close()
    conexao.close()

def adicionar_usuario_padrao():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = %s", ('trackland@hotmail.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO usuarios (username, password)
            VALUES (%s, %s)
        ''', (os.getenv('LOGIN'), os.getenv('LOGIN_PASSWORD')))
        conexao.commit()
    cursor.close()
    conexao.close()

# Chamar a função para criar a tabela ao iniciar a aplicação
criar_tabela_usuarios()

# Chamar a função para adicionar o usuário padrão ao iniciar a aplicação
adicionar_usuario_padrao()

def listar_tecnicos():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT nome_tecnico FROM tecnicos")
    tecnicos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return [tecnico[0] for tecnico in tecnicos]

def listar_operadoras():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT operadora FROM equipamentos")
    operadoras = cursor.fetchall()
    cursor.close()
    conexao.close()
    return [operadora[0] for operadora in operadoras]

def listar_orgaos():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT orgao FROM equipamentos")
    orgaos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return [orgao[0] for orgao in orgaos]

def listar_equipamentos_com_tecnico(tecnico):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT id_equipamento FROM equipamentos WHERE status = %s", (tecnico,))
    equipamentos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return [equip[0] for equip in equipamentos]

def listar_equipamentos_em_estoque():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT id_equipamento FROM equipamentos WHERE status = 'EM ESTOQUE'")
    equipamentos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return [equip[0] for equip in equipamentos]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conexao.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.before_request
def before_request():
    session.permanent = True
    if 'user_id' not in session and request.endpoint not in ['login', 'static']:
        return redirect(url_for('login'))

@app.route('/cadastrar_equipamento', methods=['GET', 'POST'])
def cadastrar_equipamento():
    if request.method == 'POST':
        id_equipamento = request.form['id_equipamento']
        if not id_equipamento:
            flash("ID do Equipamento é obrigatório!", "danger")
            return redirect(url_for('cadastrar_equipamento'))
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            
            id_equipamento = int(id_equipamento)
            modelo = request.form['modelo']
            imei = request.form['imei']
            observacao = request.form['observacao']
            status = "EM ESTOQUE"
            chip = None  # Definir chip como nulo
            operadora = None  # Definir operadora como nulo
            orgao = None  # Definir orgao como nulo

            # Verificar se o campo imei não está vazio antes de converter para int
            imei = int(imei) if imei else None

            query = '''
                INSERT INTO equipamentos (id_equipamento, modelo, chip, operadora, imei, status, orgao, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            valores = (id_equipamento, modelo, chip, operadora, imei, status, orgao, observacao)
            cursor.execute(query, valores)
            conexao.commit()
            flash("Equipamento cadastrado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao cadastrar equipamento: {e}", "danger")
        finally:
            cursor.close()
            conexao.close()
        return redirect(url_for('cadastrar_equipamento'))
    return render_template('cadastrar_equipamento.html')

@app.route('/cadastrar_equipamentos_em_massa', methods=['GET', 'POST'])
def cadastrar_equipamentos_em_massa():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                conexao = conectar_banco()
                cursor = conexao.cursor()
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                for _, row in df.iterrows():
                    id_equipamento = row['id_equipamento']
                    modelo = row['modelo']
                    chip = row['chip']
                    operadora = row['operadora']
                    imei = row['imei']
                    orgao = row['orgao']
                    observacao = row['observacao']
                    status = "EM ESTOQUE"

                    query = '''
                        INSERT INTO equipamentos (id_equipamento, modelo, chip, operadora, imei, status, orgao, observacao)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    '''
                    valores = (id_equipamento, modelo, chip, operadora, imei, status, orgao, observacao)
                    cursor.execute(query, valores)
                conexao.commit()
                flash("Equipamentos cadastrados com sucesso!", "success")
            except Exception as e:
                flash(f"Erro ao cadastrar equipamentos: {e}", "danger")
            finally:
                cursor.close()
                conexao.close()
        return redirect(url_for('cadastrar_equipamentos_em_massa'))
    return render_template('cadastrar_equipamentos_em_massa.html')

@app.route('/transferir_estoque_para_tecnico', methods=['GET', 'POST'])
def transferir_estoque_para_tecnico():
    tecnicos = listar_tecnicos()
    equipamentos = listar_equipamentos_em_estoque()
    if request.method == 'POST':
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            ids_equipamentos = request.form.getlist('ids_equipamentos[]')
            tecnico_destino = request.form['tecnico_destino']
            observacao = request.form['observacao']

            for id_equipamento in ids_equipamentos:
                cursor.execute("""
                    UPDATE equipamentos
                    SET status = %s
                    WHERE id_equipamento = %s
                """, (tecnico_destino, id_equipamento))
                cursor.execute("""
                    INSERT INTO movimentacoes (id_equipamento, origem, destino, data_movimentacao, tipo_movimentacao, observacao)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_equipamento, "Estoque", tecnico_destino, datetime.now(), "Transferência", observacao))
            conexao.commit()
            flash("Transferência registrada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao transferir equipamento: {e}", "danger")
        finally:
            cursor.close()
            conexao.close()
        return redirect(url_for('transferir_estoque_para_tecnico'))
    return render_template('transferir_estoque_para_tecnico.html', tecnicos=tecnicos, equipamentos=equipamentos)

@app.route('/transferir_tecnico_para_outro', methods=['GET', 'POST'])
def transferir_tecnico_para_outro():
    tecnicos = listar_tecnicos()
    ids_equipamentos = listar_equipamentos_com_tecnico(tecnicos[0]) if tecnicos else []
    if request.method == 'POST':
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            tecnico_origem = request.form['tecnico_origem']
            ids_equipamentos = request.form.getlist('id_equipamento')
            acao = request.form['acao']
            tecnico_destino = request.form.get('tecnico_destino')

            for id_equipamento in ids_equipamentos:
                if acao == "Devolver ao estoque":
                    destino = "EM ESTOQUE"
                    cursor.execute("""
                        UPDATE equipamentos
                        SET status = %s
                        WHERE id_equipamento = %s
                    """, (destino, id_equipamento))
                    cursor.execute("""
                        INSERT INTO movimentacoes (id_equipamento, origem, destino, data_movimentacao, tipo_movimentacao, observacao)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_equipamento, tecnico_origem, destino, datetime.now(), "Devolução", "Devolvido ao estoque"))
                else:
                    destino = tecnico_destino
                    cursor.execute("""
                        UPDATE equipamentos
                        SET status = %s
                        WHERE id_equipamento = %s
                    """, (destino, id_equipamento))
                    cursor.execute("""
                        INSERT INTO movimentacoes (id_equipamento, origem, destino, data_movimentacao, tipo_movimentacao, observacao)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_equipamento, tecnico_origem, destino, datetime.now(), "Transferência", "Transferido para outro técnico"))

            conexao.commit()
            flash("Transferência realizada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao transferir equipamento: {e}", "danger")
        finally:
            cursor.close()
            conexao.close()
        return redirect(url_for('transferir_tecnico_para_outro'))
    return render_template('transferir_tecnico_para_outro.html', tecnicos=tecnicos, ids_equipamentos=ids_equipamentos)

@app.route('/equipamentos_com_tecnico', methods=['GET'])
def equipamentos_com_tecnico():
    tecnico = request.args.get('tecnico')
    equipamentos = listar_equipamentos_com_tecnico(tecnico)
    return jsonify(equipamentos)

@app.route('/visualizar_estoque')
def visualizar_estoque():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM equipamentos GROUP BY status ORDER BY COUNT(*) DESC")
        resultados = cursor.fetchall()
    except Exception as e:
        flash(f"Erro ao visualizar estoque: {e}", "danger")
        resultados = []
    finally:
        cursor.close()
        conexao.close()
    return render_template('visualizar_estoque.html', resultados=resultados)

@app.route('/detalhes_estoque')
def detalhes_estoque():
    status = request.args.get('status')
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipamentos WHERE status = %s", (status,))
        equipamentos = cursor.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexao.close()
    return jsonify(equipamentos)

@app.route('/visualizar_movimentacoes')
def visualizar_movimentacoes():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        data_filtro = request.args.get('data_filtro')
        origem_filtro = request.args.get('origem_filtro')
        destino_filtro = request.args.get('destino_filtro')
        tipo_filtro = request.args.get('tipo_filtro')
        id_equipamento_filtro = request.args.get('id_equipamento_filtro')

        conexao = conectar_banco()
        cursor = conexao.cursor()

        query_base = """
            SELECT id_equipamento, origem, destino, DATE_FORMAT(data_movimentacao, '%d/%m/%y %H:%i'), tipo_movimentacao, observacao
            FROM movimentacoes
        """
        query_count = "SELECT COUNT(*) FROM movimentacoes"
        filtros = []
        valores = []

        if data_filtro:
            filtros.append("DATE(data_movimentacao) = %s")
            valores.append(data_filtro)
        if origem_filtro:
            filtros.append("origem = %s")
            valores.append(origem_filtro)
        if destino_filtro:
            filtros.append("destino = %s")
            valores.append(destino_filtro)
        if tipo_filtro:
            filtros.append("tipo_movimentacao = %s")
            valores.append(tipo_filtro)
        if id_equipamento_filtro:
            filtros.append("id_equipamento = %s")
            valores.append(id_equipamento_filtro)

        if filtros:
            query_base += " WHERE " + " AND ".join(filtros)
            query_count += " WHERE " + " AND ".join(filtros)

        query_base += " ORDER BY data_movimentacao DESC LIMIT %s OFFSET %s"
        valores.extend([per_page, offset])

        cursor.execute(query_count, valores[:-2])
        total_movimentacoes = cursor.fetchone()[0]
        total_pages = (total_movimentacoes + per_page - 1) // per_page

        cursor.execute(query_base, valores)
        resultados = cursor.fetchall()

        # Obter opções de filtros
        cursor.execute("SELECT DISTINCT origem FROM movimentacoes WHERE origem IS NOT NULL AND origem != ''")
        origens = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT destino FROM movimentacoes WHERE destino IS NOT NULL AND destino != ''")
        destinos = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT tipo_movimentacao FROM movimentacoes")
        tipos = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        flash(f"Erro ao visualizar movimentações: {e}", "danger")
        resultados = []
        total_pages = 1
        page = 1
        origens = []
        destinos = []
        tipos = []
    finally:
        cursor.close()
        conexao.close()
    return render_template('visualizar_movimentacoes.html', resultados=resultados, total_pages=total_pages, current_page=page, data_filtro=data_filtro, origens=origens, destinos=destinos, tipos=tipos, id_equipamento_filtro=id_equipamento_filtro)

@app.route('/status_estoque')
def status_estoque():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM equipamentos GROUP BY status")
        resultados = cursor.fetchall()
        status_list = [{"local": status, "quantidade": count} for status, count in resultados]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexao.close()
    return jsonify(status_list)

@app.route('/opcoes_filtros')
def opcoes_filtros():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT DISTINCT origem FROM movimentacoes")
        origens = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT destino FROM movimentacoes")
        destinos = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT tipo_movimentacao FROM movimentacoes")
        tipos = [row[0] for row in cursor.fetchall()]
        
        return jsonify({
            'origens': origens,
            'destinos': destinos,
            'tipos': tipos
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexao.close()

@app.route('/opcoes_filtros_equipamentos')
def opcoes_filtros_equipamentos():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT DISTINCT modelo FROM equipamentos")
        modelos = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT operadora FROM equipamentos")
        operadoras = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT orgao FROM equipamentos")
        orgaos = [row[0] for row in cursor.fetchall()]
        
        return jsonify({
            'modelos': modelos,
            'operadoras': operadoras,
            'orgaos': orgaos
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexao.close()

@app.route('/filtrar_equipamentos')
def filtrar_equipamentos():
    filtros = {
        'id_equipamento': request.args.get('id'),  # Corrigir o nome do campo para id_equipamento
        'modelo': request.args.get('modelo'),
        'chip': request.args.get('chip'),
        'operadora': request.args.get('operadora'),
        'imei': request.args.get('imei'),
        'orgao': request.args.get('orgao'),
        'observacao': request.args.get('observacao'),
        'status': request.args.get('status')  # Adicionar o filtro de status
    }
    
    query = "SELECT * FROM equipamentos WHERE 1=1"
    valores = []
    
    for campo, valor in filtros.items():
        if valor:
            query += f" AND {campo} LIKE %s"
            valores.append(f"%{valor}%")
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(query, valores)
        equipamentos = cursor.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conexao.close()
    
    return jsonify(equipamentos)

@app.route('/cadastrar_equipamentos_portal', methods=['GET', 'POST'])
def cadastrar_equipamentos_portal():
    if request.method == 'POST':
        portal = request.form['portal']
        iccid = request.form['iccid']
        apn_domain = request.form['apn_domain']
        telefone_completo = request.form['telefone_completo']
        id_tracker = request.form['id_tracker']
        tracker_template_code = request.form['tracker_template_code']
        imei = request.form.get('imei')

        # Ajustar o valor do tracker_template_code
        if tracker_template_code == "RST / Absolut Evo (ASCII)":
            tracker_template_code = "123"

        # Função para cadastrar no portal SSX
        if (portal == 'SSX'):
            flash("Cadastro no portal SSX deve ser feito na rota /cadastrar_ssx.", "danger")
        else:
            flash("Portal não suportado ainda.", "danger")
        return redirect(url_for('cadastrar_equipamentos_portal'))
    return render_template('cadastrar_equipamentos_portal.html')

@app.route('/cadastrar_ssx', methods=['GET', 'POST'])
def cadastrar_ssx():
    if request.method == 'POST':
        id_tracker = request.form['id_tracker']
        iccid = request.form['iccid']
        operadora = request.form['apn_domain']
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        # Verificar se o equipamento está no estoque
        cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE id_equipamento = %s", (id_tracker,))
        if cursor.fetchone()[0] == 0:
            flash("Equipamento não está no estoque!", "danger")
            return render_template('cadastrar_ssx.html', flash_message="Equipamento não está no estoque!", is_success=False)
        
        # Verificar se o ICCID existe na tabela de simcards e obter a operadora
        cursor.execute("SELECT operadora FROM simcards WHERE chip = %s", (iccid,))
        simcard = cursor.fetchone()
        if not simcard:
            flash("ICCID não encontrado na tabela de SIMCards!", "danger")
            return render_template('cadastrar_ssx.html', flash_message="ICCID não encontrado na tabela de SIMCards!", is_success=False)
        operadora = simcard[0]

        # Verificar se o SIMCard já está vinculado a outro equipamento
        cursor.execute("SELECT id_equipamento FROM equipamentos WHERE chip = %s", (iccid,))
        equipamento_antigo = cursor.fetchone()
        if equipamento_antigo:
            # Desvincular o SIMCard do equipamento antigo
            cursor.execute("UPDATE equipamentos SET chip = NULL, operadora = NULL WHERE id_equipamento = %s", (equipamento_antigo[0],))

        portal = request.form['portal']
        apn_domain = request.form['apn_domain']
        telefone_completo = request.form['telefone_completo']
        tracker_template_code = request.form['tracker_template_code']
        imei = request.form.get('imei')

        # Ajustar o valor do tracker_template_code
        if tracker_template_code == "RST / Absolut Evo (ASCII)":
            tracker_template_code = "123"

        # Função para cadastrar no portal SSX
        url_login = "https://integration.systemsatx.com.br/Login"
        params = {
            "Username": os.getenv('SSX_USERNAME'),
            "Password": os.getenv('SSX_PASSWORD')
        }
        response = requests.post(url_login, params=params)
        if response.status_code != 200:
            flash(f"Erro ao obter o token: {response.status_code}", "danger")
        else:
            response_json = response.json()
            token = response_json.get("AccessToken")
            if not token:
                flash("AccessToken não encontrado na resposta.", "danger")
            else:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                country_calling_code = telefone_completo[:2]
                area_calling_code = telefone_completo[2:5]
                phone_number = telefone_completo[5:]
                simcard_payload = {
                    "ICCID": iccid,
                    "APNDomain": apn_domain,
                    "CountryCallingCode": country_calling_code,
                    "AreaCallingCode": area_calling_code,
                    "PhoneNumber": phone_number,
                    "BillingCylcleEndDay": None,
                    "Price": None,
                    "MegabyteLimit": None,
                    "PIN": None,
                    "PUK": None
                }
                simcard_url = "https://integration.systemsatx.com.br/Administration/SimCard/Insert"
                simcard_response = requests.post(simcard_url, json=simcard_payload, headers=headers)
                if (simcard_response.status_code == 200 or "ICCID already exists" in simcard_response.text):
                    register_url = "https://integration.systemsatx.com.br/Administration/Tracker/Insert"
                    payload = {
                        "IdTracker": id_tracker,
                        "TrackerTemplateIntegrationCode": tracker_template_code,
                        "ICCID1": iccid
                    }
                    if imei:
                        payload["IMEI"] = imei
                    register_response = requests.post(register_url, json=payload, headers=headers)
                    if register_response.status_code == 200:
                        # Atualizar os campos "orgao", "chip" e "operadora" do equipamento no banco de dados
                        cursor.execute("UPDATE equipamentos SET orgao = %s, chip = %s, operadora = %s WHERE id_equipamento = %s", (portal, iccid, operadora, id_tracker))
                        conexao.commit()
                        flash("Cadastrado com sucesso!", "success")
                        return render_template('cadastrar_ssx.html', flash_message="Cadastrado com sucesso!", is_success=True)
                    else:
                        flash("Erro ao cadastrar equipamento.", "danger")
                        return render_template('cadastrar_ssx.html', flash_message="Erro ao cadastrar equipamento.", is_success=False)
                else:
                    flash("Erro ao cadastrar SIMCard.", "danger")
                    return render_template('cadastrar_ssx.html', flash_message="Erro ao cadastrar SIMCard.", is_success=False)
        cursor.close()
        conexao.close()
        return redirect(url_for('cadastrar_ssx'))
    return render_template('cadastrar_ssx.html')

@app.route('/cadastrar_fulltrack', methods=['GET', 'POST'])
def cadastrar_fulltrack():
    if request.method == 'POST':
        ras_ras_id_aparelho = request.form['ras_ras_id_aparelho']
        ras_ras_chip = request.form['ras_ras_chip']
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        # Verificar se o equipamento está no estoque
        cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE id_equipamento = %s", (ras_ras_id_aparelho,))
        if cursor.fetchone()[0] == 0:
            flash("Equipamento não está no estoque!", "danger")
            return render_template('cadastrar_fulltrack.html', flash_message="Equipamento não está no estoque!", is_success=False)
        
        # Verificar se o ID do chip existe na tabela de simcards e obter a operadora
        cursor.execute("SELECT operadora FROM simcards WHERE chip = %s", (ras_ras_chip,))
        simcard = cursor.fetchone()
        if not simcard:
            flash("ID do chip não encontrado na tabela de SIMCards!", "danger")
            return render_template('cadastrar_fulltrack.html', flash_message="ID do chip não encontrado na tabela de SIMCards!", is_success=False)
        operadora = simcard[0]

        # Verificar se o SIMCard já está vinculado a outro equipamento
        cursor.execute("SELECT id_equipamento FROM equipamentos WHERE chip = %s", (ras_ras_chip,))
        equipamento_antigo = cursor.fetchone()
        if equipamento_antigo:
            # Desvincular o SIMCard do equipamento antigo
            cursor.execute("UPDATE equipamentos SET chip = NULL, operadora = NULL WHERE id_equipamento = %s", (equipamento_antigo[0],))

        ras_ras_prd_id = int(request.form['ras_ras_prd_id'])
        ras_ras_imei = request.form['ras_ras_imei']

        url = "https://ws.fulltrack2.com/trackers/save"
        headers = {
            "apikey": os.getenv('API_KEY'),
            "secretkey": os.getenv('SECRET_KEY'),
            "Content-Type": "application/json"
        }
        data = {
            "ras_ras_id_aparelho": ras_ras_id_aparelho,
            "ras_ras_prd_id": ras_ras_prd_id,
            "ras_ras_chip": ras_ras_chip,
            "ras_ras_linha": None,
            "ras_ras_imei": ras_ras_imei
        }

        response = requests.put(url, json=data, headers=headers)
        if response.status_code == 200:
            # Atualizar os campos "orgao", "chip" e "operadora" do equipamento no banco de dados
            cursor.execute("UPDATE equipamentos SET orgao = %s, chip = %s, operadora = %s WHERE id_equipamento = %s", ("FULLTRACK", ras_ras_chip, operadora, ras_ras_id_aparelho))
            conexao.commit()
            flash("Cadastrado com sucesso!", "success")
            return render_template('cadastrar_fulltrack.html', flash_message="Cadastrado com sucesso!", is_success=True)
        else:
            flash(f"Erro ao cadastrar equipamento: {response.json()}", "danger")
            return render_template('cadastrar_fulltrack.html', flash_message=f"Erro ao cadastrar equipamento: {response.json()}", is_success=False)
        
        cursor.close()
        conexao.close()
        return redirect(url_for('cadastrar_fulltrack'))
    return render_template('cadastrar_fulltrack.html')

@app.route('/cadastrar_multiportal', methods=['GET', 'POST'])
def cadastrar_multiportal():
    # Implementação futura para cadastro no portal MULTIPORTAL
    return render_template('cadastrar_multiportal.html')

@app.route('/verificar_equipamento')
def verificar_equipamento():
    id_equipamento = request.args.get('id_equipamento')
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE id_equipamento = %s", (id_equipamento,))
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    conexao.close()
    return jsonify({"exists": exists})

@app.route('/cadastrar_simcard', methods=['GET', 'POST'])
def cadastrar_simcard():
    if request.method == 'POST':
        chips = request.form['chip'].split(';')
        operadora = request.form['operadora']
        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()
            for chip in chips:
                chip = chip.strip()
                if chip:
                    query = '''
                        INSERT INTO simcards (chip, operadora)
                        VALUES (%s, %s)
                    '''
                    valores = (chip, operadora)
                    cursor.execute(query, valores)
            conexao.commit()
            flash("SIMCard cadastrado com sucesso!", "success")
            return redirect(url_for('cadastrar_simcard', success=True))
        except Exception as e:
            flash(f"Erro ao cadastrar SIMCards: {e}", "danger")
            return redirect(url_for('cadastrar_simcard', error=True))
        finally:
            cursor.close()
            conexao.close()
    return render_template('cadastrar_simcard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

@app.template_filter('datetimeformat')
def datetimeformat(value):
    if isinstance(value, str):
        value = datetime.strptime(value, '%d/%m/%y %H:%M')
    return value.strftime('%d/%m/%y %H:%M')

def comparar_equipamentos():
    # URL para obter o token
    auth_url = "https://integration.systemsatx.com.br/Login"
    auth_params = {
        "Username": "paulo_victor@ufms.br",
        "Password": "paulovictor999"
    }

    # Fazer a requisição para obter o token
    auth_response = requests.post(auth_url, params=auth_params)

    # Verificar se a autenticação foi bem-sucedida
    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        access_token = auth_data.get("AccessToken")

        # Configurar o cabeçalho com o token
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        # URL da segunda requisição
        tracker_url = "https://integration.systemsatx.com.br/Administration/Tracker/List"

        # Corpo da requisição
        payload = {
            "PropertyName": "TrackerIntegrationCode",
            "Condition": "Equal"
        }

        # Fazer a requisição POST
        tracker_response = requests.post(tracker_url, json=payload, headers=headers)

        # Verificar a resposta
        if tracker_response.status_code == 200:
            tracker_data = tracker_response.json()
            ids_tracker = [item.get('IdTracker') for item in tracker_data if item.get('TrackedUnitType') == 1]

            if ids_tracker:
                try:
                    conexao = conectar_banco()
                    cursor = conexao.cursor()
                    cursor.execute("SELECT id_equipamento, status FROM equipamentos WHERE status != 'INSTALADO'")
                    equipamentos = cursor.fetchall()
                    ids_equipamentos = {equip[0]: equip[1] for equip in equipamentos}

                    for id_tracker in ids_tracker:
                        if id_tracker in ids_equipamentos and ids_equipamentos[id_tracker] != 'EM ESTOQUE':
                            tecnico = ids_equipamentos[id_tracker]
                            cursor.execute("""
                                UPDATE equipamentos
                                SET status = 'INSTALADO'
                                WHERE id_equipamento = %s
                            """, (id_tracker,))
                            cursor.execute("""
                                INSERT INTO movimentacoes (id_equipamento, origem, destino, data_movimentacao, tipo_movimentacao, observacao)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (id_tracker, tecnico, "INSTALADO", datetime.now(), "Instalação", "Equipamento instalado"))
                    conexao.commit()
                except Exception as e:
                    print(f"Erro ao atualizar equipamentos: {e}")
                finally:
                    cursor.close()
                    conexao.close()
            else:
                print("Nenhum equipamento com TrackedUnitType igual a 1 encontrado.")
        else:
            print(f"Erro na requisição Tracker/List: {tracker_response.status_code}, {tracker_response.text}")
    else:
        print(f"Erro na autenticação: {auth_response.status_code}, {auth_response.text}")

def verificar_equipamentos_fulltrack():
    url = "https://ws.fulltrack2.com/trackers/all"
    headers = {
        "apikey": "f8c496428711c7dea7347ea76ffa4733cdd9c406",
        "secretkey": "3a7e6572ccdedb8f8e0996f9ecca8bf9d017b4dc"
    }

    response = requests.get(url, headers=headers)

    try:
        data = response.json()  # Converte para JSON

        # Descobre a chave que contém a lista de dados
        key_for_list = next((key for key in data if isinstance(data[key], list)), None)

        if key_for_list:
            trackers = data[key_for_list]  # Pega a lista correta

            conexao = conectar_banco()
            cursor = conexao.cursor()

            for item in trackers:
                ras_ras_id_aparelho = item.get("ras_ras_id_aparelho", "N/A")
                ras_ras_cli_id = item.get("ras_ras_cli_id", None)

                if ras_ras_cli_id:
                    cursor.execute("SELECT status FROM equipamentos WHERE id_equipamento = %s", (ras_ras_id_aparelho,))
                    equipamento = cursor.fetchone()

                    if equipamento and equipamento[0] != 'INSTALADO':
                        tecnico = equipamento[0]
                        cursor.execute("""
                            UPDATE equipamentos
                            SET status = 'INSTALADO'
                            WHERE id_equipamento = %s
                        """, (ras_ras_id_aparelho,))
                        cursor.execute("""
                            INSERT INTO movimentacoes (id_equipamento, origem, destino, data_movimentacao, tipo_movimentacao, observacao)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (ras_ras_id_aparelho, tecnico, "INSTALADO", datetime.now(), "Instalação", "Equipamento instalado"))

            conexao.commit()
            cursor.close()
            conexao.close()
        else:
            print("Erro: Não foi encontrada uma lista dentro do JSON.")

    except requests.exceptions.JSONDecodeError:
        print("Erro: A resposta não está em formato JSON válido.", response.text)

# Configurar o agendador
scheduler = BackgroundScheduler()
scheduler.add_job(func=comparar_equipamentos, trigger="interval", minutes=1)
scheduler.add_job(func=verificar_equipamentos_fulltrack, trigger="interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

