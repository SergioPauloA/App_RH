import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import threading
import time
from datetime import datetime
import os
import queue
import pyperclip

class WhatsAppSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Valkyrie.Bot")
        self.root.geometry("700x750")  # Aumentei um pouco a altura
        self.root.configure(bg='#1e1e1e')
        self.root.iconbitmap(r"C:\Users\sergio.andrade\Documents\Valkyrie\Valkyrie.ico")

        # Cores do tema
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'highlight_bg': '#3d3d3d',
            'frame_bg': '#2d2d2d'
        }

        # Variáveis de controle
        self.numeros_var = tk.StringVar()
        self.running = False
        self.driver = None
        self.login_confirmado = False
        self.usuario_logado = self.get_username()

        # Fila para comunicação entre threads
        self.message_queue = queue.Queue()

        # Configuração da interface
        self.setup_interface()

        # Iniciar thread de monitoramento de mensagens
        self.message_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.message_thread.start()

    def get_username(self):
        """
        Obtém o nome de usuário do sistema operacional.
        """
        try:
            # Para Windows
            if os.name == 'nt':
                return os.getlogin()
            # Para sistemas Unix-like
            else:
                return os.getenv('USER') or getpass.getuser()
        except Exception as e:
            print(f"Erro ao obter nome de usuário: {e}")
            return "Usuário"

    def setup_interface(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Título
        titulo_label = tk.Label(main_frame, text= f"Bem vindo {self.usuario_logado.title()}", 
                                font=("Arial", 16, "bold"), 
                                bg=self.colors['bg'], 
                                fg=self.colors['fg'])
        titulo_label.pack(pady=10)

        # Frame para entrada de números
        numeros_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        numeros_frame.pack(fill='x', pady=5)

        tk.Label(numeros_frame, text="Números (separados por vírgula):", 
                 bg=self.colors['bg'], 
                 fg=self.colors['fg']).pack(side='left', padx=5)
        
        numeros_entry = tk.Entry(numeros_frame, 
                                 textvariable=self.numeros_var, 
                                 width=50, 
                                 bg=self.colors['highlight_bg'], 
                                 fg=self.colors['fg'])
        numeros_entry.pack(side='left', padx=5, expand=True, fill='x')

        # Frame para mensagem
        mensagem_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        mensagem_frame.pack(fill='x', pady=5)

        tk.Label(mensagem_frame, text="Mensagem:", 
                 bg=self.colors['bg'], 
                 fg=self.colors['fg']).pack(side='left', padx=5)
        
        # Campo de texto para mensagem
        self.mensagem_text = tk.Text(main_frame, 
                                     height=18, 
                                     width=80, 
                                     bg=self.colors['highlight_bg'], 
                                     fg=self.colors['fg'], 
                                     wrap=tk.WORD)
        self.mensagem_text.pack(pady=(15, 5), expand=True, fill='x')  # Aumenta o espaço acima

        # Frame para botões
        botoes_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        botoes_frame.pack(pady=10)

        # Botão de Login
        self.login_button = tk.Button(botoes_frame, text="Login WhatsApp", 
                                      command=self.fazer_login_whatsapp, 
                                      bg=self.colors['highlight_bg'], 
                                      fg=self.colors['fg'],
                                      width=20)
        self.login_button.pack(side=tk.LEFT, padx=5)

        # Botão de Desbloquear Manual
        self.desbloquear_button = tk.Button(botoes_frame, text="Desbloquear", 
                                            command=self.desbloquear_manual, 
                                            bg='#4CAF50', 
                                            fg=self.colors['fg'],
                                            width=20)
        self.desbloquear_button.pack(side=tk.LEFT, padx=5)

        # Botão de Enviar
        self.enviar_button = tk.Button(botoes_frame, text="Pronto", 
                                       command=self.iniciar_envio, 
                                       bg=self.colors['highlight_bg'], 
                                       fg=self.colors['fg'], 
                                       state=tk.DISABLED,
                                       width=20)
        self.enviar_button.pack(side=tk.LEFT, padx=5)

        # Terminal de saída
        self.output_text = scrolledtext.ScrolledText(main_frame, 
                                                     wrap=tk.WORD, 
                                                     height=10, 
                                                     bg='#000000', 
                                                     fg='#00ff00', 
                                                     font=('Courier', 10))
        self.output_text.pack(expand=True, fill='both', padx=5, pady=5)
        

    def desbloquear_manual(self):
        """
        Método para desbloqueio manual dos botões
        """
        self.login_confirmado = True
        self.enviar_button.config(state=tk.NORMAL)
        self.log("Desbloqueio manual realizado. Você pode enviar mensagens agora.")

    def log(self, mensagem):
        """
        Thread-safe logging method
        """
        self.message_queue.put(('log', mensagem))

    def process_messages(self):
        """
        Process messages from the queue in the main thread
        """
        while True:
            try:
                # Bloqueia até receber uma mensagem
                msg_type, msg_content = self.message_queue.get()
                
                if msg_type == 'log':
                    # Usa after para garantir que a atualização ocorra na thread principal
                    self.root.after(0, self._update_log, msg_content)
                elif msg_type == 'button_state':
                    # Atualiza o estado do botão na thread principal
                    self.root.after(0, self._update_button_state, msg_content)
                
                self.message_queue.task_done()
            except Exception as e:
                print(f"Erro no processamento de mensagens: {e}")

    def _update_log(self, mensagem):
        """
        Atualiza o log na thread principal
        """
        try:
            self.output_text.configure(state='normal')
            self.output_text.insert(tk.END, mensagem + '\n')
            self.output_text.see(tk.END)
            self.output_text.configure(state='disabled')
        except Exception as e:
            print(f"Erro ao atualizar log: {e}")

    def _update_button_state(self, state_info):
        """
        Atualiza o estado do botão na thread principal
        """
        button_type, text, state = state_info
        if button_type == 'login':
            self.login_button.config(text=text, state=state)
        elif button_type == 'enviar':
            self.enviar_button.config(text=text, state=state)

    def fazer_login_whatsapp(self):
        # Disable login button during process
        self.message_queue.put(('button_state', ('login', "Fazendo Login...", tk.DISABLED)))

        # Start login in a separate thread
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        try:
            # Configurar WebDriver
            opt = EdgeOptions()
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=opt)

            self.log("Abrindo WhatsApp Web...")
            
            # Verifica se já está logado em alguma janela
            try:
                self.driver.get("https://web.whatsapp.com/")
                
                # Tenta encontrar elementos que indicam login
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='chat-list-search']"))
                )
                
                self.login_confirmado = True
                self.log(f"Login já realizado, {self.usuario_logado}!")
                
                # Atualizar botão de login e habilitar botão de envio
                self.message_queue.put(('button_state', ('login', "Login WhatsApp", tk.NORMAL)))
                self.message_queue.put(('button_state', ('enviar', "Pronto", tk.NORMAL)))
                return
            
            except:
                # Se não estiver logado, aguarda QR Code
                self.log("Por favor, escaneie o QR Code no navegador...")
                self.log("IMPORTANTE: Se o login não for detectado, use o botão 'Desbloquear'")
            
            # Aguardar login por QR Code com timeout
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='chat-list-search']"))
            )

            self.login_confirmado = True
            self.log(f"Login realizado com sucesso, {self.usuario_logado}!")
            
            # Atualizar botão de login e habilitar botão de envio
            self.message_queue.put(('button_state', ('login', "Login WhatsApp", tk.NORMAL)))
            self.message_queue.put(('button_state', ('enviar', "Pronto", tk.NORMAL)))
            
        except Exception as e:
            self.log(f"Erro durante o login: {str(e)}")
            self.log("IMPORTANTE: Se o login não foi detectado, use o botão 'Desbloquear'")
            
            # Reabilitar botão de login se falhar
            self.message_queue.put(('button_state', ('login', "Login WhatsApp", tk.NORMAL)))

    # Restante do código permanece igual ao anterior
    
    def iniciar_envio(self):
        # Validar entradas
        numeros = self.numeros_var.get().strip()
        mensagem = self.mensagem_text.get("1.0", tk.END).strip()

        if not numeros or not mensagem:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos.")
            return

        # Validar login
        if not self.login_confirmado:
            messagebox.showwarning("Aviso", "Faça login no WhatsApp primeiro!")
            return

        # Disable the button during sending
        self.message_queue.put(('button_state', ('enviar', "Enviando...", tk.DISABLED)))

        # Limpar terminal
        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.configure(state='disabled')

        # Iniciar thread de envio
        self.running = True
        threading.Thread(target=self.enviar_whatsapp, daemon=True).start()

    def enviar_whatsapp(self):
        try:
            # Preparar números
            numeros = [num.strip() for num in self.numeros_var.get().split(',')]
            mensagem = self.mensagem_text.get("1.0", tk.END).strip()
    
            # Enviar mensagens
            total_numeros = len(numeros)
            for index, numero in enumerate(numeros, 1):
                if not self.running:
                    break
    
                self.log(f"Enviando mensagem para {numero} ({index}/{total_numeros})")
                
                try:
                    # Acessar conversa
                    driver_url = f"https://web.whatsapp.com/send?phone={numero}"
                    self.driver.get(driver_url)
                    
                    # Espera flexível para carregamento da página
                    try:
                        # Aguardar tempo suficiente para carregamento
                        time.sleep(10)
                        
                        # Verificar se o campo de mensagem está visível
                        campo_mensagem = WebDriverWait(self.driver, 20).until(
                            EC.element_to_be_clickable((By.XPATH, "//*[@id='main']/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div[1]/p"))
                        )
                    except Exception as wait_error:
                        self.log(f"Erro ao localizar campo de mensagem: {wait_error}")
                        # Tentar capturar qualquer erro de página
                        try:
                            # Verifica se há alguma mensagem de erro na página
                            erro_elementos = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'número inválido') or contains(text(), 'não encontrado')]")
                            if erro_elementos:
                                self.log(f"Erro de número para {numero}: {erro_elementos[0].text}")
                            else:
                                # Screenshot para diagnóstico
                                self.driver.save_screenshot(f"erro_pagina_{numero}.png")
                                self.log(f"Página não carregou corretamente para {numero}")
                        except Exception as debug_error:
                            self.log(f"Erro adicional de diagnóstico: {debug_error}")
                        
                        # Pula para próximo número
                        continue
    
                    # Método de envio usando pyperclip para mensagem única
                    try:
                        # Copiar mensagem para área de transferência
                        pyperclip.copy(mensagem)
                        
                        # Localizar campo de mensagem
                        campo_mensagem = self.driver.find_element(By.XPATH, "//*[@id='main']/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div[1]/p")
                        
                        # Limpar campo (se necessário)
                        campo_mensagem.clear()
                        
                        # Colar mensagem
                        # Usar combinação de teclas Ctrl+V para colar
                        campo_mensagem.send_keys(Keys.CONTROL + 'v')
                        
                        # Enviar mensagem
                        campo_mensagem.send_keys(Keys.ENTER)
                        
                        self.log(f"Mensagem enviada para {numero}")
                        time.sleep(5)
    
                    except Exception as send_error:
                        self.log(f"Erro ao enviar mensagem para {numero}: {send_error}")
                        # Screenshot para diagnóstico
                        self.driver.save_screenshot(f"erro_envio_{numero}.png")
                        continue
    
                except Exception as e:
                    # Log detalhado do erro
                    self.log(f"Erro completo ao processar {numero}: {type(e).__name__}")
                    self.log(f"Detalhes do erro: {str(e)}")
                    
                    # Tempo de espera maior entre tentativas para evitar bloqueios
                    time.sleep(10)
    
                # Tempo adicional entre envios para reduzir chance de bloqueio
                time.sleep(5)
    
            # Mensagem de conclusão personalizada
            hora_atual = datetime.now().hour
            if hora_atual < 12:
                mensagem_final = f"Pronto {self.usuario_logado.title()}, tenha um ótimo dia!"
            elif hora_atual < 18:
                mensagem_final = f"Pronto {self.usuario_logado.title()}, tenha uma ótima tarde!"
            else:
                mensagem_final = f"Pronto {self.usuario_logado.title()}, tenha uma ótima noite!"
            
            self.log(mensagem_final)
    
        except Exception as e:
            # Log de erro global
            self.log(f"Erro global durante o processo: {type(e).__name__}")
            self.log(f"Detalhes do erro global: {str(e)}")
    
        finally:
            # Reabilitar botão de envio
            self.message_queue.put(('button_state', ('enviar', "Pronto", tk.NORMAL)))
            self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()
