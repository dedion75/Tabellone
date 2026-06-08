import random
import math
import struct
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.core.audio import SoundLoader, Sound

# --- MOTORE AUDIO SINTETICO ---
class SuonoSintetico(Sound):
    @staticmethod
    def crea_bip(frequenza, durata, tipo="bip"):
        frequenza_campionamento = 22050
        num_campioni = int(durata * frequenza_campionamento)
        dati = bytearray()
        
        for i in range(num_campioni):
            t = float(i) / frequenza_campionamento
            valore = math.sin(2.0 * math.pi * frequenza * t)
            
            if tipo == "sordo":
                valore = (valore + random.uniform(-0.7, 0.7)) * math.exp(-5 * t)
                
            campione = int(valore * 32767)
            dati.extend(struct.pack('<h', max(-32767, min(32767, campione))))
            
        wav_header = struct.pack('<4sI4s4sIHHIIHH4sI', 
            b'RIFF', 36 + len(dati), b'WAVE', b'fmt ', 16, 1, 1, 
            frequenza_campionamento, frequenza_campionamento * 2, 2, 16, b'data', len(dati))
        
        from tempfile import NamedTemporaryFile
        f = NamedTemporaryFile(delete=False, suffix='.wav')
        f.write(wav_header + dati)
        f.close()
        return SoundLoader.load(f.name)

# --- BOTTONE TONDO PERSONALIZZATO ---
class BottoneTondo(Button):
    def __init__(self, colore_spento, colore_acceso, **kwargs):
        super().__init__(**kwargs)
        self.colore_spento = colore_spento
        self.colore_acceso = colore_acceso
        self.background_normal = ''
        self.background_color = [0, 0, 0, 0]
        
        with self.canvas.before:
            self.graphics_color = Color(rgba=self.colore_spento)
            self.graphics_ellipse = Ellipse(pos=self.pos, size=self.size)
            
        self.bind(pos=self.aggiorna_grafica, size=self.aggiorna_grafica)

    def aggiorna_grafica(self, *args):
        self.graphics_ellipse.pos = self.pos
        self.graphics_ellipse.size = self.size

    def imposta_stato(self, acceso=False):
        if acceso:
            self.graphics_color.rgba = self.colore_acceso
        else:
            self.graphics_color.rgba = self.colore_spento

# --- LOGICA DEL GIOCO ---
class GiocoBottoniTondi(App):
    def build(self):
        self.colori_spenti = [[0.4, 0, 0, 1], [0, 0.4, 0, 1], [0, 0, 0.4, 1], [0.4, 0.4, 0, 1], [0.4, 0, 0.4, 1]]
        self.colori_accesi = [[1, 0.2, 0.2, 1], [0.2, 1, 0.2, 1], [0.2, 0.2, 1, 1], [1, 1, 0.2, 1], [1, 0.2, 1, 1]]
        
        self.suono_bip = SuonoSintetico.crea_bip(frequenza=880, durata=0.15, tipo="bip")
        self.suono_errore = SuonoSintetico.crea_bip(frequenza=120, durata=0.25, tipo="sordo")
        
        self.layout_principale = FloatLayout()
        self.inizializza_gioco()
        return self.layout_principale

    def inizializza_gioco(self):
        self.layout_principale.clear_widgets()
        
        self.punteggio = 0
        self.bottone_attivo = None
        self.tempo_corrente = 3.0    
        self.livello_corrente = 0    
        self.tempo_rimasto_partita = 60 
        
        self.evento_timer = None     
        self.evento_partita = None
        
        self.label_info = Label(
            text=f"Punti: {self.punteggio}  |  Ritmo: {self.tempo_corrente:.1f}s  |  Tempo: {self.tempo_rimasto_partita}s", 
            font_size='20sp',
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'top': 0.95}
        )
        self.layout_principale.add_widget(self.label_info)
        
        posizioni = [
            {'center_x': 0.30, 'center_y': 0.65},
            {'center_x': 0.70, 'center_y': 0.65},
            {'center_x': 0.50, 'center_y': 0.45},
            {'center_x': 0.30, 'center_y': 0.25},
            {'center_x': 0.70, 'center_y': 0.25}
        ]
        
        self.lista_bottoni = []
        for i in range(5):
            btn = BottoneTondo(
                colore_spento=self.colori_spenti[i],
                colore_acceso=self.colori_accesi[i],
                text=f"{i+1}",
                font_size='24sp',
                size_hint=(None, None),
                size=('85dp', '85dp'),
                pos_hint=posizioni[i]
            )
            btn.id_index = i 
            btn.bind(on_press=self.controlla_click)
            self.lista_bottoni.append(btn)
            self.layout_principale.add_widget(btn)
            
        self.avvia_nuovo_timer()
        self.evento_partita = Clock.schedule_interval(self.aggiorna_tempo_partita, 1.0)
        Clock.schedule_once(self.accendi_bottone, 0.5)

    def avvia_nuovo_timer(self):
        if self.evento_timer:
            Clock.unschedule(self.evento_timer)
        self.evento_timer = Clock.schedule_interval(self.accendi_bottone, self.tempo_corrente)

    def accendi_bottone(self, dt):
        # NUOVA REGOLA: Se c'era un bottone attivo non premuto, togli 5 punti
        if self.bottone_attivo is not None:
            self.punteggio = max(0, self.punteggio - 5)
            if self.suono_errore:
                self.suono_errore.play()
            self.aggiorna_testo_interfaccia()

        self.spegni_tutti()
        self.bottone_attivo = random.randint(0, 4)
        self.lista_bottoni[self.bottone_attivo].imposta_stato(acceso=True)

    def spegni_tutti(self):
        for i in range(5):
            self.lista_bottoni[i].imposta_stato(acceso=False)
        self.bottone_attivo = None

    def aggiorna_tempo_partita(self, dt):
        self.tempo_rimasto_partita -= 1
        self.aggiorna_testo_interfaccia()
        if self.tempo_rimasto_partita <= 0:
            self.termina_gioco()

    def aggiorna_testo_interfaccia(self):
        self.label_info.text = f"Punti: {self.punteggio}  |  Ritmo: {self.tempo_corrente:.1f}s  |  Tempo: {self.tempo_rimasto_partita}s"

    def controlla_click(self, instance):
        if self.tempo_rimasto_partita <= 0:
            return
            
        if self.bottone_attivo == instance.id_index:
            self.punteggio += 10
            if self.suono_bip: 
                self.suono_bip.play()
            
            # Azzera lo stato attivo *prima* di spegnere, così il timer successivo sa che abbiamo colpito in tempo
            self.bottone_attivo = None
            self.spegni_tutti()
            
            nuovo_livello = self.punteggio // 30
            if nuovo_livello > self.livello_corrente:
                self.livello_corrente = nuovo_livello
                self.tempo_corrente = max(0.6, self.tempo_corrente - 0.4)
                self.avvia_nuovo_timer()
        else:
            self.punteggio = max(0, self.punteggio - 15)
            if self.suono_errore: 
                self.suono_errore.play()
                
        self.aggiorna_testo_interfaccia()

    def terminates_gioco(self):
        pass # Correzione typo: viene sovrascritto sotto da termina_gioco

    def termina_gioco(self):
        if self.evento_timer: Clock.unschedule(self.evento_timer)
        if self.evento_partita: Clock.unschedule(self.evento_partita)
        self.spegni_tutti()
        
        self.layout_principale.clear_widgets()
        
        lbl_game_over = Label(
            text=f"GAME OVER\nPunteggio Finale: {self.punteggio}",
            font_size='32sp',
            halign='center',
            size_hint=(1, 0.4),
            pos_hint={'x': 0, 'y': 0.5}
        )
        
        btn_riavvia = Button(
            text="Rigioca",
            font_size='24sp',
            size_hint=(0.5, 0.15),
            pos_hint={'center_x': 0.5, 'center_y': 0.3}
        )
        btn_riavvia.bind(on_press=lambda instance: self.inizializza_gioco())
        
        self.layout_principale.add_widget(lbl_game_over)
        self.layout_principale.add_widget(btn_riavvia)

if __name__ == '__main__':
    GiocoBottoniTondi().run()
