import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from datetime import datetime
import pandas as pd

# Função para conectar ao banco de dados
def conectar_banco():
    return mysql.connector.connect(
        host='srv1310.hstgr.io',
        user='u834686159_paulo',
        password='Monitora753',
        database='u834686159_conectividade'
    )

# Conexão inicial com o banco de dados
conexao = conectar_banco()
cursor = conexao.cursor()

# Função para garantir que a conexão está ativa
def garantir_conexao():
    global conexao, cursor
    try:
        conexao.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {err}")
        conexao = conectar_banco()
        cursor = conexao.cursor()

def listar_ids_equipamentos():
    garantir_conexao()
    cursor.execute("SELECT id_equipamento FROM equipamentos")
    return [row[0] for row in cursor.fetchall()]

def listar_ids_equipamentos_em_estoque():
    garantir_conexao()
    cursor.execute("SELECT id_equipamento FROM equipamentos WHERE status = 'EM ESTOQUE'")
    return [row[0] for row in cursor.fetchall()]

def listar_tecnicos():
    garantir_conexao()
    cursor.execute("SELECT id_tecnico, nome_tecnico FROM tecnicos")
    return cursor.fetchall()

def registrar_movimentacao(id_equipamento, origem, destino, tipo, observacao):
    try:
        garantir_conexao()
        cursor.execute("""
            INSERT INTO movimentacoes (id_equipamento, origem, destino, data_movimentacao, tipo_movimentacao, observacao)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_equipamento, origem, destino, datetime.now(), tipo, observacao))
        conexao.commit()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao registrar movimentação: {e}")

def visualizar_estoque():
    garantir_conexao()
    janela = tk.Toplevel()
    janela.title("Visualizar Estoque")
    janela.geometry("600x400")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    cursor.execute("SELECT status, COUNT(*) FROM equipamentos GROUP BY status")
    resultados = cursor.fetchall()

    tree = ttk.Treeview(janela, columns=("Status", "Quantidade"), show="headings")
    tree.heading("Status", text="Status")
    tree.heading("Quantidade", text="Quantidade")
    tree.pack(fill=tk.BOTH, expand=True)

    for row in resultados:
        tree.insert("", tk.END, values=row)

def visualizar_movimentacoes():
    garantir_conexao()
    janela = tk.Toplevel()
    janela.title("Visualizar Movimentações")
    janela.geometry("1300x500")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    cursor.execute("SELECT id_equipamento, origem, destino, DATE_FORMAT(data_movimentacao, '%d/%m/%y'), tipo_movimentacao, observacao FROM movimentacoes ORDER BY data_movimentacao DESC")
    resultados = cursor.fetchall()

    tree = ttk.Treeview(janela, columns=("ID Equipamento", "Origem", "Destino", "Data Movimentação", "Tipo Movimentação", "Observação"), show="headings")
    tree.heading("ID Equipamento", text="ID Equipamento")
    tree.heading("Origem", text="Origem")
    tree.heading("Destino", text="Destino")
    tree.heading("Data Movimentação", text="Data Movimentação")
    tree.heading("Tipo Movimentação", text="Tipo Movimentação")
    tree.heading("Observação", text="Observação")
    tree.pack(fill=tk.BOTH, expand=True)

    for row in resultados:
        tree.insert("", tk.END, values=row)

class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list

    def autocomplete(self, delta=0):
        if delta:
            self.delete(self.position, tk.END)
        else:
            self.position = len(self.get())
        _hits = [item for item in self._completion_list if item.lower().startswith(self.get().lower())]
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        if _hits:
            self._hit_index = (self._hit_index + delta) % len(_hits)
            self.delete(0, tk.END)
            self.insert(0, _hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down'):
            return
        if event.keysym == 'Return':
            self.autocomplete()
        else:
            self.autocomplete()

def cadastrar_equipamento():
    def salvar():
        try:
            garantir_conexao()
            id_equipamento = int(entry_id.get())
            modelo = combo_modelo.get()
            chip = int(entry_chip.get())
            operadora = combo_operadora.get()
            imei = int(entry_imei.get())
            orgao = combo_orgao.get()
            observacao = entry_obs.get()
            status = "EM ESTOQUE"

            query = '''
                INSERT INTO equipamentos (id_equipamento, modelo, chip, operadora, imei, status, orgao, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            valores = (id_equipamento, modelo, chip, operadora, imei, status, orgao, observacao)
            cursor.execute(query, valores)
            conexao.commit()
            messagebox.showinfo("Sucesso", "Equipamento cadastrado com sucesso!")
            janela.destroy()
        except ValueError:
            messagebox.showerror("Erro", "ID do Equipamento, Chip e IMEI devem ser números inteiros.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar equipamento: {e}")

    janela = tk.Toplevel()
    janela.title("Cadastrar Equipamento")
    janela.geometry("600x600")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    frame = tk.Frame(janela, bg='lightgrey')
    frame.pack(expand=True, padx=20, pady=20)

    for widget in frame.winfo_children():
        widget.grid_configure(padx=10, pady=10)

    tk.Label(frame, text="ID do Equipamento:", font=("Arial", 12), bg='lightgrey').grid(row=0, column=0, sticky='e')
    entry_id = tk.Entry(frame, font=("Arial", 12), width=32)
    entry_id.grid(row=0, column=1)

    tk.Label(frame, text="Modelo:", font=("Arial", 12), bg='lightgrey').grid(row=1, column=0, sticky='e')
    combo_modelo = ttk.Combobox(frame, values=["RST LC 4G", "RST-2G", "RST-4G", "VIRLOC", "SATELITAL"], font=("Arial", 12), width=30, state="readonly")
    combo_modelo.grid(row=1, column=1)

    tk.Label(frame, text="Chip:", font=("Arial", 12), bg='lightgrey').grid(row=2, column=0, sticky='e')
    entry_chip = tk.Entry(frame, font=("Arial", 12), width=32)
    entry_chip.grid(row=2, column=1)

    tk.Label(frame, text="Operadora:", font=("Arial", 12), bg='lightgrey').grid(row=3, column=0, sticky='e')
    combo_operadora = ttk.Combobox(frame, values=["AVATEK", "ALLCOM", "LYRA"], font=("Arial", 12), width=30, state="readonly")
    combo_operadora.grid(row=3, column=1)

    tk.Label(frame, text="IMEI:", font=("Arial", 12), bg='lightgrey').grid(row=4, column=0, sticky='e')
    entry_imei = tk.Entry(frame, font=("Arial", 12), width=32)
    entry_imei.grid(row=4, column=1)

    tk.Label(frame, text="Órgão:", font=("Arial", 12), bg='lightgrey').grid(row=5, column=0, sticky='e')
    combo_orgao = ttk.Combobox(frame, values=["FULLTRACK", "MULTIPORTAL", "SSX"], font=("Arial", 12), width=30, state="readonly")
    combo_orgao.grid(row=5, column=1)

    tk.Label(frame, text="Observação:", font=("Arial", 12), bg='lightgrey').grid(row=6, column=0, sticky='e')
    entry_obs = tk.Entry(frame, font=("Arial", 12), width=32)
    entry_obs.grid(row=6, column=1)

    tk.Button(frame, text="Salvar", command=salvar, font=("Arial", 12), bg="lightblue", width=20, height=2).grid(row=7, column=0, columnspan=2, pady=20)

def cadastrar_equipamentos_em_massa():
    def carregar_arquivo():
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                for _, row in df.iterrows():
                    garantir_conexao()
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
                messagebox.showinfo("Sucesso", "Equipamentos cadastrados com sucesso!")
                janela.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao cadastrar equipamentos: {e}")

    janela = tk.Toplevel()
    janela.title("Cadastrar Equipamentos em Massa")
    janela.geometry("400x400")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    frame = tk.Frame(janela, bg='lightgrey')
    frame.pack(expand=True, padx=20, pady=20)

    tk.Label(frame, text="Selecione o arquivo CSV ou XLSX:", font=("Arial", 12), bg='lightgrey').pack(pady=10)
    tk.Button(frame, text="Carregar Arquivo", command=carregar_arquivo, font=("Arial", 12), bg="lightblue", width=20, height=2).pack(pady=10)
    tk.Label(frame, text="Baixe o modelo de arquivo em XLSX:", font=("Arial", 12), bg='lightgrey').pack(pady=10)
    tk.Button(frame, text="Download Modelo", command=lambda: filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile="modelo_equipamento.xlsx"), font=("Arial", 12), bg="lightblue", width=20, height=2).pack(pady=10)

def transferir_estoque_para_tecnico():
    def salvar():
        try:
            garantir_conexao()
            ids_equipamentos = [listbox_ids.get(i) for i in listbox_ids.curselection()]
            tecnico_destino = combo_tecnico.get()

            if not ids_equipamentos:
                lbl_erro.config(text="Selecione pelo menos um equipamento", fg="red")
                return

            tecnicos_existentes = [tec[1] for tec in listar_tecnicos()]
            if tecnico_destino not in tecnicos_existentes:
                lbl_erro.config(text="Esse técnico não existe", fg="red")
                return

            for id_equipamento in ids_equipamentos:
                cursor.execute("""
                    UPDATE equipamentos
                    SET status = %s
                    WHERE id_equipamento = %s
                """, (tecnico_destino, id_equipamento))
                registrar_movimentacao(id_equipamento, "Estoque", tecnico_destino, "Transferência", "Transferido do estoque para técnico")
            conexao.commit()
            messagebox.showinfo("Sucesso", "Transferência registrada com sucesso!")
            janela.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao transferir equipamento: {e}")

    def filtrar_ids(event):
        search_term = entry_pesquisa.get().lower()
        selected_ids = [listbox_ids.get(i) for i in listbox_ids.curselection()]
        listbox_ids.delete(0, tk.END)
        for id_equipamento in listar_ids_equipamentos_em_estoque():
            if search_term in str(id_equipamento).lower():
                listbox_ids.insert(tk.END, id_equipamento)
                if id_equipamento in selected_ids:
                    listbox_ids.selection_set(tk.END)

    janela = tk.Toplevel()
    janela.title("Transferir do Estoque para Técnico")
    janela.geometry("600x400")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    frame = tk.Frame(janela, bg='lightgrey')
    frame.pack(expand=True, padx=20, pady=20)

    for widget in frame.winfo_children():
        widget.grid_configure(padx=10, pady=10)

    tk.Label(frame, text="Técnico de Destino:", font=("Arial", 12), bg='lightgrey').grid(row=0, column=0, sticky='e')
    combo_tecnico = AutocompleteCombobox(frame, font=("Arial", 12), width=30)
    combo_tecnico.set_completion_list([tec[1] for tec in listar_tecnicos()])
    combo_tecnico.grid(row=0, column=1)

    tk.Label(frame, text="Pesquisar ID do Equipamento:", font=("Arial", 12), bg='lightgrey').grid(row=1, column=0, sticky='e')
    entry_pesquisa = tk.Entry(frame, font=("Arial", 12), width=32)
    entry_pesquisa.grid(row=1, column=1)
    entry_pesquisa.bind('<KeyRelease>', filtrar_ids)
    entry_pesquisa.bind('<FocusIn>', lambda event: entry_pesquisa.selection_clear())

    tk.Label(frame, text="IDs dos Equipamentos:", font=("Arial", 12), bg='lightgrey').grid(row=2, column=0, sticky='e')
    listbox_ids = tk.Listbox(frame, selectmode=tk.MULTIPLE, font=("Arial", 12), width=32, height=5)
    for id_equipamento in listar_ids_equipamentos_em_estoque():
        listbox_ids.insert(tk.END, id_equipamento)
    listbox_ids.grid(row=2, column=1)

    lbl_erro = tk.Label(frame, text="", font=("Arial", 12), bg='lightgrey')
    lbl_erro.grid(row=3, column=0, columnspan=2)

    tk.Button(frame, text="Salvar", command=salvar, font=("Arial", 12), bg="lightblue", width=20, height=2).grid(row=4, column=0, columnspan=2, pady=20)

def transferir_tecnico_para_outro():
    def salvar():
        try:
            garantir_conexao()
            tecnico_origem = combo_origem.get()
            id_equipamento = combo_id.get()
            acao = combo_acao.get()
            tecnico_destino = combo_destino.get()

            tecnicos_existentes = [tec[1] for tec in listar_tecnicos()]
            if tecnico_origem not in tecnicos_existentes:
                lbl_erro.config(text="Esse técnico de origem não existe", fg="red")
                return

            if id_equipamento not in listar_ids_equipamentos():
                lbl_erro.config(text="Esse equipamento não existe", fg="red")
                return

            if acao == "Devolver ao estoque":
                destino = "Estoque"
                cursor.execute("""
                    UPDATE equipamentos
                    SET status = 'EM ESTOQUE'
                    WHERE id_equipamento = %s
                """, (id_equipamento,))
                registrar_movimentacao(id_equipamento, tecnico_origem, destino, "Devolução", "Devolvido ao estoque")
            else:
                if tecnico_destino not in tecnicos_existentes:
                    lbl_erro.config(text="Esse técnico de destino não existe", fg="red")
                    return
                destino = tecnico_destino
                cursor.execute("""
                    UPDATE equipamentos
                    SET status = %s
                    WHERE id_equipamento = %s
                """, (destino, id_equipamento))
                registrar_movimentacao(id_equipamento, tecnico_origem, destino, "Transferência", "Transferido para outro técnico")

            conexao.commit()
            messagebox.showinfo("Sucesso", "Transferência realizada com sucesso!")
            janela.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao transferir equipamento: {e}")

    def atualizar_visibilidade_tecnico_destino(event):
        if combo_acao.get() == "Devolver ao estoque":
            lbl_tecnico_destino.grid_remove()
            combo_destino.grid_remove()
        else:
            lbl_tecnico_destino.grid()
            combo_destino.grid()

    janela = tk.Toplevel()
    janela.title("Transferir entre Técnicos ou para o Estoque")
    janela.geometry("600x500")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    frame = tk.Frame(janela, bg='lightgrey')
    frame.pack(expand=True, padx=20, pady=20)

    for widget in frame.winfo_children():
        widget.grid_configure(padx=10, pady=10)

    tk.Label(frame, text="Técnico de Origem:", font=("Arial", 12), bg='lightgrey').grid(row=0, column=0, sticky='e')
    combo_origem = AutocompleteCombobox(frame, font=("Arial", 12), width=30)
    combo_origem.set_completion_list([tec[1] for tec in listar_tecnicos()])
    combo_origem.grid(row=0, column=1)

    tk.Label(frame, text="ID do Equipamento:", font=("Arial", 12), bg='lightgrey').grid(row=1, column=0, sticky='e')
    combo_id = AutocompleteCombobox(frame, font=("Arial", 12), width=30)
    combo_id.set_completion_list(listar_ids_equipamentos())
    combo_id.grid(row=1, column=1)

    tk.Label(frame, text="Ação:", font=("Arial", 12), bg='lightgrey').grid(row=2, column=0, sticky='e')
    combo_acao = ttk.Combobox(frame, values=["Devolver ao estoque", "Transferir para outro técnico"], font=("Arial", 12), width=30, state="readonly")
    combo_acao.grid(row=2, column=1)
    combo_acao.bind("<<ComboboxSelected>>", atualizar_visibilidade_tecnico_destino)

    lbl_tecnico_destino = tk.Label(frame, text="Técnico de Destino:", font=("Arial", 12), bg='lightgrey')
    lbl_tecnico_destino.grid(row=3, column=0, sticky='e')
    combo_destino = AutocompleteCombobox(frame, font=("Arial", 12), width=30)
    combo_destino.set_completion_list([tec[1] for tec in listar_tecnicos()])
    combo_destino.grid(row=3, column=1)

    lbl_erro = tk.Label(frame, text="", font=("Arial", 12), bg='lightgrey')
    lbl_erro.grid(row=4, column=0, columnspan=2)

    tk.Button(frame, text="Salvar", command=salvar, font=("Arial", 12), bg="lightblue", width=20, height=2).grid(row=5, column=0, columnspan=2, pady=20)

    atualizar_visibilidade_tecnico_destino(None)

def realizar_instalacao():
    def salvar():
        try:
            garantir_conexao()
            id_equipamento = combo_id.get()
            tecnico = combo_tecnico.get()

            if id_equipamento not in listar_ids_equipamentos():
                lbl_erro.config(text="Esse equipamento não existe", fg="red")
                return

            tecnicos_existentes = [tec[1] for tec in listar_tecnicos()]
            if tecnico not in tecnicos_existentes:
                lbl_erro.config(text="Esse técnico não existe", fg="red")
                return

            cursor.execute("""
                SELECT status FROM equipamentos
                WHERE id_equipamento = %s
            """, (id_equipamento,))
            status_atual = cursor.fetchone()
            if not status_atual or status_atual[0] != tecnico:
                messagebox.showerror("Erro", "O equipamento não está com o técnico selecionado.")
                return

            cursor.execute("""
                UPDATE equipamentos
                SET status = 'INSTALADO'
                WHERE id_equipamento = %s
            """, (id_equipamento,))
            registrar_movimentacao(id_equipamento, tecnico, "Instalado", "Instalação", "Equipamento instalado")
            conexao.commit()
            messagebox.showinfo("Sucesso", "Equipamento instalado com sucesso!")
            janela.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao instalar equipamento: {e}")

    janela = tk.Toplevel()
    janela.title("Instalar Equipamento")
    janela.geometry("600x400")
    janela.configure(bg='lightgrey')
    aplicar_estilos(janela)

    frame = tk.Frame(janela, bg='lightgrey')
    frame.pack(expand=True, padx=20, pady=20)

    for widget in frame.winfo_children():
        widget.grid_configure(padx=10, pady=10)

    tk.Label(frame, text="Técnico:", font=("Arial", 12), bg='lightgrey').grid(row=0, column=0, sticky='e')
    combo_tecnico = AutocompleteCombobox(frame, font=("Arial", 12), width=30)
    combo_tecnico.set_completion_list([tec[1] for tec in listar_tecnicos()])
    combo_tecnico.grid(row=0, column=1)

    tk.Label(frame, text="ID do Equipamento:", font=("Arial", 12), bg='lightgrey').grid(row=1, column=0, sticky='e')
    combo_id = AutocompleteCombobox(frame, font=("Arial", 12), width=30)
    combo_id.set_completion_list(listar_ids_equipamentos())
    combo_id.grid(row=1, column=1)

    lbl_erro = tk.Label(frame, text="", font=("Arial", 12), bg='lightgrey')
    lbl_erro.grid(row=2, column=0, columnspan=2)

    tk.Button(frame, text="Salvar", command=salvar, font=("Arial", 12), bg="lightblue", width=20, height=2).grid(row=3, column=0, columnspan=2, pady=20)

def aplicar_estilos(widget):
    estilo = ttk.Style()
    estilo.configure("TButton", font=("Arial", 12), padding=10)
    estilo.configure("TLabel", font=("Arial", 12), background='lightgrey')
    estilo.configure("TCombobox", font=("Arial", 12))
    estilo.configure("TEntry", font=("Arial", 12))
    widget.option_add("*TButton*Font", ("Arial", 12))
    widget.option_add("*TLabel*Font", ("Arial", 12))
    widget.option_add("*TCombobox*Font", ("Arial", 12))
    widget.option_add("*TEntry*Font", ("Arial", 12))

def menu_principal():
    root = tk.Tk()
    aplicar_estilos(root)
    root.title("Sistema de Gestão de Equipamentos")
    root.geometry("800x600")

    root.configure(bg="#00008B")

    frame = tk.Frame(root, bg="#00008B")
    frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    tk.Label(frame, text="TRACKLAND", font=("Arial", 25, "bold"), bg='#00008B', fg='white').pack(pady=10)

    tk.Button(frame, text="Cadastrar um Equipamento", command=cadastrar_equipamento, width=31, height=2, font=("Arial", 15), bg="lightgreen").pack(pady=0)
    tk.Button(frame, text="Cadastrar Equipamentos em Massa", command=cadastrar_equipamentos_em_massa, width=31, height=2, font=("Arial", 15), bg="lightgreen").pack(pady=0)
    tk.Button(frame, text="Transferir do Estoque para Técnico", command=transferir_estoque_para_tecnico, width=31, height=2, font=("Arial", 15), bg="lightgreen").pack(pady=0)
    tk.Button(frame, text="Transferir entre Técnicos ou Estoque", command=transferir_tecnico_para_outro, width=31, height=2, font=("Arial", 15), bg="lightgreen").pack(pady=0)
    tk.Button(frame, text="Instalar Equipamento", command=realizar_instalacao, width=31, height=2, font=("Arial", 15), bg="lightgreen").pack(pady=0)
    tk.Button(frame, text="Visualizar Estoque", command=visualizar_estoque, width=31, height=2, font=("Arial", 15), bg="lightblue").pack(pady=0)
    tk.Button(frame, text="Visualizar Movimentações", command=visualizar_movimentacoes, width=31, height=2, font=("Arial", 15), bg="lightblue").pack(pady=0)
    tk.Button(frame, text="Sair", command=root.quit, width=31, height=2, font=("Arial", 15), bg="lightcoral").pack(pady=0)

    root.mainloop()

if __name__ == "__main__":
    menu_principal()

# Fechar conexões
def fechar_conexao():
    cursor.close()
    conexao.close()

fechar_conexao()