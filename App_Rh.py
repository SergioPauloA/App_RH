import tkinter as tk
from tkinter import messagebox, scrolledtext
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

class WhatsAppSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gabi - WhatsApp Sender")
        self.root.geometry("700x700")
        self.root.configure(bg='#1e1e1e')

        # Cores do tema
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'highlight_bg': '#3d3d3d',
            'frame_bg': '#2d2d2d'
        }

        # Variáveis de controle
        self.numeros_var = tk.StringVar()
        self.mensagem_var = tk.StringVar()
        self.running = False

        # Configuração da interface
        self.setup_interface()

    def setup_interface(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Título
        titulo_label = tk.Label(main_frame, text="Gabi - WhatsApp Sender", 
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
        
        mensagem_entry = tk.Entry(mensagem_frame, 
                                  textvariable=self.mensagem_var, 
                                  width=50, 
                                  bg=self.colors['highlight_bg'], 
                                  fg=self.colors['fg'])
        mensagem_entry.pack(side='left', padx=5, expand=True, fill='x')

        # Botão de enviar
        self.enviar_button = tk.Button(main_frame, text="Enviar", 
                                  command=self.iniciar_envio, 
                                  bg=self.colors['highlight_bg'], 
                                  fg=self.colors['fg'])
        self.enviar_button.pack(pady=10)

        # Terminal de saída
        self.output_text = scrolledtext.ScrolledText(main_frame, 
                                                     wrap=tk.WORD, 
                                                     height=20, 
                                                     bg='#000000', 
                                                     fg='#00ff00', 
                                                     font=('Courier', 10))
        self.output_text.pack(expand=True, fill='both', padx=5, pady=5)

        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = tk.Scale(main_frame, 
                                     from_=0, 
                                     to=100, 
                                     orient=tk.HORIZONTAL, 
                                     length=600, 
                                     variable=self.progress_var, 
                                     showvalue=0, 
                                     bg=self.colors['bg'], 
                                     fg=self.colors['fg'], 
                                     troughcolor=self.colors['highlight_bg'])
        self.progress_bar.pack(pady=5)

    def log(self, mensagem):
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, mensagem + '\n')
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')

    def iniciar_envio(self):
        # Validar entradas
        numeros = self.numeros_var.get().strip()
        mensagem = self.mensagem_var.get().strip()

        if not numeros or not mensagem:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos.")
            return

        # Disable the button during sending
        self.enviar_button.config(state=tk.DISABLED)

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
            mensagem = self.mensagem_var.get()

            # Configurar WebDriver
            opt = EdgeOptions()
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=opt)

            # Acessar WhatsApp Web
            self.log("Abrindo WhatsApp Web...")
            driver.get("https://web.whatsapp.com/")
            
            # Aguardar login manual
            self.log("Por favor, escaneie o QR Code...")
            input("Após escanear o QR Code, pressione Enter...")

            # Enviar mensagens
            total_numeros = len(numeros)
            for index, numero in enumerate(numeros, 1):
                if not self.running:
                    break

                # Atualizar progresso
                progresso = (index / total_numeros) * 100
                self.progress_var.set(progresso)
                
                self.log(f"Enviando mensagem para {numero} ({index}/{total_numeros})")
                
                try:
                    # Acessar conversa
                    driver.get(f"https://web.whatsapp.com/send?phone={numero}&text={mensagem}")
                    time.sleep(10)

                    # Enviar mensagem
                    caixa_mensagem = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//*[@id='main']/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div[1]/p"))
                    )
                    caixa_mensagem.send_keys(Keys.ENTER)
                    
                    self.log(f"Mensagem enviada para {numero}")
                    time.sleep(5)

                except Exception as e:
                    self.log(f"Erro ao enviar para {numero}: {e}")

            # Fechar navegador
            driver.quit()

            # Mensagem de conclusão
            hora_atual = datetime.now().hour
            mensagem_final = "Pronto Gabi, tenha um ótimo dia" if hora_atual < 13 else "Pronto Gabi, tenha uma ótima tarde"
            self.log(mensagem_final)

        except Exception as e:
            self.log(f"Erro durante o processo: {e}")

        finally:
            # Reabilitar botão
            self.root.after(0, lambda: self.enviar_button.config(state=tk.NORMAL))
            self.running = False

def main():
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()