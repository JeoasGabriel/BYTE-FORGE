import heapq
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional

import pygame


# ================================================================
# INICIALIZAÇÃO
# ================================================================
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# ================================================================
# CONSTANTES DE CONFIGURAÇÃO
# ================================================================
LARGURA      = 1360
ALTURA       = 768
GRID         = 24
AREA_JOGO_Y  = 56
COLUNAS      = LARGURA // GRID
LINHAS       = (ALTURA - AREA_JOGO_Y) // GRID - 1

FPS_RENDER   = 60
FPS_BASE     = 8
FPS_MAX      = 18

THRESHOLDS_NIVEL = [0, 250, 450, 650, 1150, 1450, 1650, 2000, 2500, 3000]

MULTI_POWERUPS = [2, 3, 4, 5]
MULTI_DURACAO  = 8.0
MULTI_CHANCE   = 0.9
MULTI_CORES    = {2: (80, 220, 255), 3: (180, 80, 255), 4: (255, 160, 0), 5: (255, 60, 60)}

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake_save.json")

def _resolver_pasta_audios() -> str:
    """Procura a pasta de áudios ao lado do script, aceitando variações do nome
    (com ou sem acento) para evitar problemas de codificação entre sistemas."""
    base = os.path.dirname(os.path.abspath(__file__))
    candidatos = ["áudios", "audios", "Áudios", "Audios", "sons", "Sons"]
    for nome in candidatos:
        caminho = os.path.join(base, nome)
        if os.path.isdir(caminho):
            return caminho
    return os.path.join(base, "áudios")  # padrão, mesmo que não exista ainda

SONS_DIR = _resolver_pasta_audios()


def _carregar_som_arquivo(nome_arquivo: str, fallback=None):
    """Carrega um efeito sonoro. Procura primeiro na pasta de áudios,
    depois direto ao lado do script, depois pelo nome sem extensão."""
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    # Candidatos: pasta áudios, raiz do script, e variações sem acento
    candidatos = [
        os.path.join(SONS_DIR,    nome_arquivo),
        os.path.join(pasta_script, nome_arquivo),
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            try:
                som = pygame.mixer.Sound(caminho)
                print(f"[som] Carregado: {caminho}")
                return som
            except Exception as e:
                print(f"[aviso] Erro ao carregar '{caminho}': {e}")
    print(f"[aviso] Arquivo '{nome_arquivo}' não encontrado. Usando som procedural.")
    return fallback() if fallback else None

# Custo em moedas de cada skin
SKINS_CUSTO = {
    "classico":    0,
    "neon":       50,
    "chamas":    100,
    "gelo":      150,
    "sombra":    200,
    "dourado":   350,
    "arco_iris": 500,
    "cyber":     750,
    # Skins Animais
    "leao":      300,
    "cobra_r":   400,
    "dragao":    600,
    "tigre":     450,
}


# ================================================================
# CORES NEON/CYBERPUNK
# ================================================================
PRETO      = (5,   5,   10)
PRETO_UI   = (8,   8,   18)
VERDE      = (0,   230, 110)
VERDE_ESC  = (0,   80,  40)
VERDE_NEO  = (57,  255, 20)
VERMELHO   = (255, 60,  60)
DOURADO    = (255, 210, 0)
AZUL       = (50,  180, 255)
AZUL_ESC   = (10,  40,  90)
ROXO       = (170, 50,  255)
ROXO_BRILHO = (200, 100, 255)
BRANCO     = (240, 240, 240)
CINZA      = (80,  80,  90)
CINZA_ESC  = (30,  30,  40)
LARANJA    = (255, 140, 0)
ROSA       = (255, 80,  180)
ROSA_ESC   = (120, 20,  80)
CIANO      = (80,  220, 255)
CIANO_ESC  = (10,  60,  80)
VERDE_LIM  = (150, 255, 50)
ROXO_ESC   = (30,  10,  60)
TEAL       = (0,   200, 180)
MAGENTA    = (255, 0,   200)

# Paleta cyberpunk para UI
CYBER_BG       = (6,   6,   15)
CYBER_PANEL    = (12,  12,  28)
CYBER_BORDA    = (0,   200, 180)
CYBER_ACENTO   = (255, 0,   200)
CYBER_TEXTO    = (200, 230, 255)
CYBER_DIM      = (80,  100, 130)


# ================================================================
# TELA E RELÓGIO
# ================================================================
tela  = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake ByteForge")
clock = pygame.time.Clock()


# ================================================================
# FONTES
# ================================================================
def _font(size: int, bold: bool = False) -> pygame.font.Font:
    for nome in ("Consolas", "Courier New", "monospace"):
        try:
            return pygame.font.SysFont(nome, size, bold=bold)
        except Exception:
            pass
    return pygame.font.SysFont(None, size, bold=bold)

fonte_titulo  = _font(80, bold=True)
fonte_hud     = _font(28, bold=True)
fonte_med     = _font(40, bold=True)
fonte_peq     = _font(24)
fonte_grande  = _font(62, bold=True)
fonte_mini    = _font(16, bold=True)
fonte_ranking = _font(26, bold=True)
fonte_stat    = _font(22)


# ================================================================
# PALETAS DE SKINS
# ================================================================
PALETA_SKINS = {
    "classico":   [(0, 230, 110), (0, 160, 70)],
    "neon":       [(57, 255, 20), (0, 200, 255)],
    "chamas":     [(255, 60, 0),  (255, 180, 0)],
    "gelo":       [(130, 220, 255), (60, 130, 220)],
    "sombra":     [(80, 80, 100), (40, 40, 60)],
    "dourado":    [(255, 210, 0), (200, 140, 0)],
    "arco_iris":  None,   # calculado dinamicamente
    "cyber":      [(200, 0, 255), (0, 220, 255)],
    # Skins Animais
    "leao":       [(255, 180, 30), (200, 120, 0)],   # dourado/laranja leão
    "cobra_r":    [(30, 160, 30), (80, 220, 80)],    # verde/brilhante cobra
    "dragao":     [(180, 0, 0), (255, 80, 0)],       # vermelho/fogo dragão
    "tigre":      [(255, 140, 0), (40, 40, 40)],     # laranja/preto tigre
}

# Dicionário de padrões especiais por skin animal
SKIN_ANIMAL_TIPO = {
    "leao":    "leao",
    "cobra_r": "cobra_r",
    "dragao":  "dragao",
    "tigre":   "tigre",
}

NOMES_SKINS = {
    "classico":   "Clássico",
    "neon":       "Neon Verde",
    "chamas":     "Chamas",
    "gelo":       "Gelo Ártico",
    "sombra":     "Sombra",
    "dourado":    "Dourado",
    "arco_iris":  "Arco-Íris",
    "cyber":      "CyberSnake",
    # Animais
    "leao":       "Leao",
    "cobra_r":    "Cobra Real",
    "dragao":     "Dragao",
    "tigre":      "Tigre",
}


# ================================================================
# SISTEMA DE SAVE / PERSISTÊNCIA
# ================================================================
def _save_padrao() -> dict:
    return {
        "ranking": [],           # lista de {"pontos","nivel","data","duracao"}
        "moedas": 0,
        "skin_ativa": "classico",
        "skins_desbloqueadas": ["classico"],
        "stats": {
            "partidas_jogadas":  0,
            "mortes":            0,
            "macas_comidas":     0,
            "macas_douradas":    0,
            "inimigos_mortos":   0,
            "nivel_maximo":      1,
            "pontuacao_maxima":  0,
            "combo_maximo":      0,
            "tempo_total_s":     0,
            "power_ups_coletados": 0,
        }
    }

def carregar_save() -> dict:
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            # Garante todas as chaves existam (compatibilidade)
            padrao = _save_padrao()
            for k, v in padrao.items():
                if k not in dados:
                    dados[k] = v
            if "stats" in dados:
                for k, v in padrao["stats"].items():
                    if k not in dados["stats"]:
                        dados["stats"][k] = v
            return dados
        except Exception:
            pass
    return _save_padrao()

def salvar_save(dados: dict) -> None:
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SAVE] Erro ao salvar: {e}")

def registrar_partida(dados: dict, pontos: int, nivel: int,
                      duracao_s: float, stats_partida: dict) -> bool:
    """
    Atualiza o save com os resultados de uma partida.
    Retorna True se entrou no top-10.
    """
    s = dados["stats"]

    # Estatísticas gerais
    s["partidas_jogadas"]    += 1
    s["mortes"]              += 1
    s["macas_comidas"]       += stats_partida.get("macas", 0)
    s["macas_douradas"]      += stats_partida.get("douradas", 0)
    s["inimigos_mortos"]     += stats_partida.get("inimigos", 0)
    s["power_ups_coletados"] += stats_partida.get("powerups", 0)
    s["combo_maximo"]         = max(s["combo_maximo"], stats_partida.get("combo_max", 0))
    s["nivel_maximo"]         = max(s["nivel_maximo"], nivel)
    s["pontuacao_maxima"]     = max(s["pontuacao_maxima"], pontos)
    s["tempo_total_s"]       += duracao_s

    # Moedas: 1 moeda a cada 20 pontos
    dados["moedas"] += max(1, pontos // 20)

    # Ranking top-10
    entrada = {
        "pontos":   pontos,
        "nivel":    nivel,
        "data":     datetime.now().strftime("%d/%m/%Y %H:%M"),
        "duracao":  int(duracao_s),
    }
    dados["ranking"].append(entrada)
    dados["ranking"].sort(key=lambda x: x["pontos"], reverse=True)
    dados["ranking"] = dados["ranking"][:10]

    # Verifica se desbloqueou skins pela pontuação de moedas totais acumuladas
    _verificar_desbloqueios(dados)

    salvar_save(dados)
    return any(e is entrada for e in dados["ranking"])

def _verificar_desbloqueios(dados: dict) -> None:
    # Apenas garante que skins gratuitas (custo 0) estejam desbloqueadas.
    # Skins pagas SÓ são desbloqueadas pela compra manual (comprar_skin).
    for skin, custo in SKINS_CUSTO.items():
        if custo == 0 and skin not in dados["skins_desbloqueadas"]:
            dados["skins_desbloqueadas"].append(skin)

def comprar_skin(dados: dict, skin: str) -> bool:
    custo = SKINS_CUSTO.get(skin, 9999)
    if dados["moedas"] >= custo and skin not in dados["skins_desbloqueadas"]:
        dados["moedas"] -= custo
        dados["skins_desbloqueadas"].append(skin)
        salvar_save(dados)
        return True
    return False

def _fmt_tempo(segundos: int) -> str:
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


# ================================================================
# ASSETS — imagens
# ================================================================
def _carregar_imagem_menu() -> Optional[pygame.Surface]:
    nomes = ["menu_bg.jpg", "menu_bg.png", "IMG-20260428-WA0008.jpg"]
    pasta = os.path.dirname(os.path.abspath(__file__))
    for nome in nomes:
        caminho = os.path.join(pasta, nome)
        if os.path.exists(caminho):
            try:
                img = pygame.image.load(caminho).convert()
                return pygame.transform.scale(img, (LARGURA, ALTURA))
            except Exception:
                pass
    return None

def _desenhar_maca_vetorial(surf: pygame.Surface, dourada: bool = False) -> None:
    size    = surf.get_width()
    r_shine = max(2, size // 6)
    cabo_x  = size // 2
    if dourada:
        cor_corpo  = (255, 200, 0);  cor_brilho = (255, 240, 120, 200);  cor_sombra = (200, 120, 0, 140)
    else:
        cor_corpo  = (220, 30, 30);  cor_brilho = (255, 160, 160, 180);  cor_sombra = (160, 10, 10, 120)
    pygame.draw.ellipse(surf, cor_corpo,  (1, 3, size-2, size-4))
    pygame.draw.ellipse(surf, cor_brilho, (size//4, 4, r_shine*2, r_shine))
    pygame.draw.ellipse(surf, cor_sombra, (4, size//2, size-8, size//2-4))
    pygame.draw.line(surf, (100, 60, 10), (cabo_x, 2), (cabo_x+2, 0), 2)
    pygame.draw.ellipse(surf, (30, 180, 40), (cabo_x, 0, size//4, size//6))

def _carregar_ou_criar_sprite(nome: str, dourada: bool = False) -> pygame.Surface:
    pasta = os.path.dirname(os.path.abspath(__file__))
    for caminho in [os.path.join(pasta, nome), os.path.join(os.getcwd(), nome)]:
        if os.path.exists(caminho):
            try:
                img = pygame.image.load(caminho)
                # Garante surface com canal alpha independente do formato do arquivo
                img = img.convert_alpha()
                # Escala para o tamanho correto da grade
                scaled = pygame.transform.smoothscale(img, (GRID-2, GRID-2))
                return scaled
            except Exception as e:
                print(f"[aviso] Erro ao carregar sprite '{nome}': {e}")
    # Fallback vetorial com transparência garantida
    surf = pygame.Surface((GRID-2, GRID-2), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))  # limpa com transparência total antes de desenhar
    _desenhar_maca_vetorial(surf, dourada=dourada)
    return surf

IMAGEM_MENU    = _carregar_imagem_menu()
SPRITE_MACA    = _carregar_ou_criar_sprite("sprite_0.png",        dourada=False)
SPRITE_DOURADA = _carregar_ou_criar_sprite("sprite_dourada.png",  dourada=True)


# ================================================================
# SONS PROCEDURAIS
# ================================================================
def _montar_som(buf: list) -> pygame.mixer.Sound:
    arr = bytearray()
    for s in buf:
        arr += s.to_bytes(2, byteorder="little", signed=True)
    return pygame.mixer.Sound(buffer=bytes(arr))

def _gerar_onda(sr: int, dur: float, gerador) -> list:
    n = int(sr * dur); buf = []
    for i in range(n):
        v = gerador(i, n, sr); val = max(-32768, min(32767, int(v * 32767)))
        buf += [val, val]
    return buf

def _som_comer() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.08,
        lambda i,n,sr: math.sin(2*math.pi*(440+220*i/n)*i/sr)*(1-i/n)*0.4))

def _som_morte() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.6,
        lambda i,n,sr: (math.sin(2*math.pi*(300-250*i/n)*i/sr)+random.uniform(-0.1,0.1))*(1-i/n)*0.5))

def _som_power() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.3,
        lambda i,n,sr: math.sin(2*math.pi*(200+600*i/n)*i/sr)*math.sin(math.pi*i/n)*0.5))

def _som_nivel() -> pygame.mixer.Sound:
    sr, buf = 44100, []
    for nota in [523, 659, 784, 1047]:
        n = int(sr*0.1)
        for i in range(n):
            buf += [max(-32768,min(32767,int(math.sin(2*math.pi*nota*i/sr)*math.sin(math.pi*i/n)*0.4*32767)))]*2
    return _montar_som(buf)

def _som_multi_powerup() -> pygame.mixer.Sound:
    sr, buf = 44100, []
    for nota in [523, 659, 784, 880, 1047]:
        n = int(sr*0.07)
        for i in range(n):
            buf += [max(-32768,min(32767,int(math.sin(2*math.pi*nota*i/sr)*math.sin(math.pi*i/n)*0.45*32767)))]*2
    return _montar_som(buf)

def _som_multi_expirar() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.25,
        lambda i,n,sr: math.sin(2*math.pi*(800-500*i/n)*i/sr)*(1-i/n)*0.35))

def _som_beep(freq=440, dur=0.05, vol=0.3) -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, dur,
        lambda i,n,sr: math.sin(2*math.pi*freq*i/sr)*min(1.0,(n-i)/(n*0.1))*vol))

def _som_emboscada() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.35,
        lambda i,n,sr: math.sin(2*math.pi*(180+40*math.sin(i/sr*12))*i/sr)*math.sin(math.pi*i/n)*0.3))

def _som_moeda() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.12,
        lambda i,n,sr: math.sin(2*math.pi*880*i/sr)*math.sin(math.pi*i/n)*0.35))

def _som_desbloqueio() -> pygame.mixer.Sound:
    sr, buf = 44100, []
    for nota in [440, 554, 659, 880]:
        n = int(sr*0.09)
        for i in range(n):
            buf += [max(-32768,min(32767,int(math.sin(2*math.pi*nota*i/sr)*math.sin(math.pi*i/n)*0.5*32767)))]*2
    return _montar_som(buf)

# ================================================================
# MÚSICAS PROCEDURAIS (geradas com ondas senoidais)
# ================================================================

def _gerar_musica_menu(duracao_s: float = 8.0) -> pygame.mixer.Sound:
    """Música ambiente cyberpunk para o menu — arpejo lento e suave."""
    sr = 22050
    notas_arp = [261, 329, 392, 523, 659, 523, 392, 329]  # Dó maior arpejo
    dur_nota  = duracao_s / len(notas_arp)
    buf = []
    for idx, freq in enumerate(notas_arp * 2):
        n = int(sr * dur_nota)
        for i in range(n):
            t_i = i / sr
            # Onda principal (senoidal suave)
            onda  = math.sin(2*math.pi*freq*t_i) * 0.18
            # Harmônico suave
            onda += math.sin(2*math.pi*freq*2*t_i) * 0.06
            # Sub-grave pulsante
            onda += math.sin(2*math.pi*(freq*0.5)*t_i) * 0.04
            # Envelope ADSR simples
            env = min(i/(n*0.08), 1.0) * max(0.0, 1.0 - (i-n*0.85)/max(1,n*0.15))
            val = max(-32768, min(32767, int(onda * env * 32767)))
            buf += [val, val]
    return _montar_som(buf)

def _gerar_musica_gameplay(duracao_s: float = 12.0) -> pygame.mixer.Sound:
    """Música de gameplay — ritmo mais rápido e tenso."""
    sr = 22050
    # Sequência pentatônica menor (tensão)
    seq = [220, 261, 293, 349, 392, 440, 392, 349, 293, 261, 220, 196]
    dur_nota = duracao_s / len(seq)
    buf = []
    for idx, freq in enumerate(seq):
        n = int(sr * dur_nota)
        for i in range(n):
            t_i = i / sr
            fase = idx * 0.5
            onda  = math.sin(2*math.pi*freq*t_i + fase) * 0.14
            onda += math.sin(2*math.pi*freq*3*t_i) * 0.04   # 3ª harmônica
            # Pulso rítmico (simula bateria eletrônica)
            beat_rate = 4.0  # BPM relativo
            beat = math.sin(2*math.pi*beat_rate*t_i)
            if beat > 0.95:
                onda += 0.08 * math.exp(-(t_i % (1/beat_rate)) * 30)
            env = min(i/(n*0.05), 1.0) * max(0.0, 1.0-(i-n*0.9)/max(1,n*0.1))
            val = max(-32768, min(32767, int(onda * env * 32767)))
            buf += [val, val]
    return _montar_som(buf)

def _gerar_musica_gameover(duracao_s: float = 4.0) -> pygame.mixer.Sound:
    """Música de game over — melodia descendente e triste."""
    sr = 22050
    notas = [392, 349, 329, 293, 261, 220, 196, 174]  # Sol descendo
    dur_nota = duracao_s / len(notas)
    buf = []
    for freq in notas:
        n = int(sr * dur_nota)
        for i in range(n):
            t_i = i / sr
            onda  = math.sin(2*math.pi*freq*t_i) * 0.20
            onda += math.sin(2*math.pi*freq*0.5*t_i) * 0.08  # subgrave
            # Vibrato leve
            vib = 1.0 + 0.01*math.sin(2*math.pi*5*t_i)
            onda *= vib
            env = min(i/(n*0.05), 1.0) * max(0.0, 1.0-(i-n*0.7)/max(1,n*0.3))
            val = max(-32768, min(32767, int(onda * env * 32767)))
            buf += [val, val]
    return _montar_som(buf)

def _gerar_musica_vitoria(duracao_s: float = 3.0) -> pygame.mixer.Sound:
    """Fanfarra de vitória — ascendente e brilhante."""
    sr = 22050
    notas = [261, 329, 392, 523, 659, 784, 1047]
    dur_nota = duracao_s / len(notas)
    buf = []
    for freq in notas:
        n = int(sr * dur_nota)
        for i in range(n):
            t_i = i / sr
            onda  = math.sin(2*math.pi*freq*t_i) * 0.22
            onda += math.sin(2*math.pi*freq*2*t_i) * 0.08
            onda += math.sin(2*math.pi*freq*3*t_i) * 0.04
            env = min(i/(n*0.03), 1.0) * max(0.0, 1.0-(i-n*0.8)/max(1,n*0.2))
            val = max(-32768, min(32767, int(onda * env * 32767)))
            buf += [val, val]
    return _montar_som(buf)

# ================================================================
# GERENCIADOR DE MÚSICA DE FUNDO
# ================================================================
class MusicaFundo:
    """Gerencia a reprodução em loop de músicas de fundo por contexto.
    Usa os áudios reais cortados (pasta 'sons/') quando disponíveis,
    caindo para a música procedural gerada como reserva."""

    # Mapeia cada contexto/modo para o arquivo de música real correspondente
    ARQUIVOS = {
        "menu":         "menu_music.mp3",
        "classico":     "modo_classico.mp3",
        "gameplay":     "modo_classico.mp3",   # alias (modo clássico)
        "time_attack":  "modo_classico.mp3",
        "multi_versus": "modo_classico.mp3",
        "endless":      "modo_endless.mp3",
        "hardcore":     "modo_hardcore.mp3",
        "boss_rush":    "modo_hardcore.mp3",
    }

    def __init__(self):
        self._canal    = pygame.mixer.Channel(7)  # canal reservado para música
        self._atual    = None   # nome do contexto atual
        self._sons     = {}     # cache de sounds (arquivo real ou procedural)
        self._volume   = 0.35

    def _obter_som(self, contexto: str):
        if contexto in self._sons:
            return self._sons[contexto]

        som = None
        arquivo = self.ARQUIVOS.get(contexto)
        if arquivo:
            pasta_script = os.path.dirname(os.path.abspath(__file__))
            for pasta in [SONS_DIR, pasta_script]:
                caminho = os.path.join(pasta, arquivo)
                if os.path.exists(caminho):
                    try:
                        som = pygame.mixer.Sound(caminho)
                        print(f"[música] Carregada: {caminho}")
                        break
                    except Exception as e:
                        print(f"[aviso] Erro ao carregar música '{caminho}': {e}")
            if som is None:
                print(f"[aviso] Música '{arquivo}' não encontrada; usando procedural.")

        if som is None:
            # Reserva: música procedural antiga, caso o arquivo real falhe
            if contexto in ("menu",):
                som = _gerar_musica_menu(8.0)
            elif contexto in ("classico", "gameplay", "time_attack", "multi_versus",
                              "endless", "hardcore", "boss_rush"):
                som = _gerar_musica_gameplay(12.0)
            elif contexto == "vitoria":
                som = _gerar_musica_vitoria(3.0)
            else:
                return None

        self._sons[contexto] = som
        return som

    def tocar(self, contexto: str) -> None:
        if contexto == self._atual:
            return
        self._atual = contexto
        self._canal.stop()
        som = self._obter_som(contexto)
        if som:
            som.set_volume(self._volume)
            self._canal.play(som, loops=-1)  # loop infinito até ser parado

    def parar(self) -> None:
        self._atual = None
        self._canal.stop()

    def game_over(self) -> None:
        """Para a música em loop do modo e toca o som de game over (uma única vez)."""
        self._atual = None
        self._canal.stop()
        if SOM_GAMEOVER:
            SOM_GAMEOVER.play()

    def set_volume(self, v: float) -> None:
        self._volume = max(0.0, min(1.0, v))
        if self._canal.get_busy():
            self._canal.set_volume(self._volume)

    def acelerar(self, nivel: int) -> None:
        """Acelera e aumenta o pitch da música conforme o nível sobe (nível 1=normal, nível 10=1.8x)."""
        if self._atual is None:
            return
        # Fator de aceleração: nível 1 → 1.0x, nível 10 → 1.8x
        fator = 1.0 + (min(nivel, 10) - 1) * 0.089
        # Usa cache do original para não acumular acelerações
        chave_orig = f"__original_{self._atual}"
        if chave_orig not in self._sons:
            som_base = self._sons.get(self._atual)
            if som_base is None:
                return
            self._sons[chave_orig] = som_base
        som_original = self._sons[chave_orig]
        try:
            import numpy as np
            raw = pygame.sndarray.array(som_original)
            n_orig = len(raw)
            n_novo = max(1, int(n_orig / fator))
            indices = np.linspace(0, n_orig - 1, n_novo).astype(np.int32)
            raw_acelerado = raw[indices]
            som_novo = pygame.sndarray.make_sound(raw_acelerado)
            som_novo.set_volume(self._volume)
            self._sons[self._atual] = som_novo
            self._canal.stop()
            self._canal.play(som_novo, loops=-1)
        except Exception as e:
            print(f"[aviso] acelerar música: {e}")


# Sons de efeito por contexto específico
def _som_explosao() -> pygame.mixer.Sound:
    """Explosão ao morrer — burst ruidoso descendente."""
    sr = 44100; dur = 0.5; n = int(sr*dur); buf = []
    for i in range(n):
        t_i = i/sr
        noise = random.uniform(-1, 1)
        decay = math.exp(-t_i*8)
        sweep = math.sin(2*math.pi*(200-180*t_i/dur)*t_i)
        onda  = (noise*0.5 + sweep*0.5) * decay * 0.55
        val   = max(-32768, min(32767, int(onda*32767)))
        buf  += [val, val]
    return _montar_som(buf)

def _som_nivel_up_especial() -> pygame.mixer.Sound:
    """Efeito ao subir de nível — crescendo brilhante."""
    sr = 44100; buf = []
    for nota in [523, 659, 784, 880, 1047, 1318]:
        n = int(sr*0.08)
        for i in range(n):
            onda = math.sin(2*math.pi*nota*i/sr) * math.sin(math.pi*i/n) * 0.45
            val  = max(-32768, min(32767, int(onda*32767)))
            buf += [val, val]
    return _montar_som(buf)

def _som_powerup_especial() -> pygame.mixer.Sound:
    """Efeito ao pegar power-up — shwoosh ascendente."""
    sr = 44100; dur = 0.35; n = int(sr*dur); buf = []
    for i in range(n):
        t_i = i/sr
        freq = 300 + 800 * (t_i/dur)**0.5
        onda = math.sin(2*math.pi*freq*t_i) * math.sin(math.pi*t_i/dur) * 0.45
        val  = max(-32768, min(32767, int(onda*32767)))
        buf += [val, val]
    return _montar_som(buf)

def _som_tutorial_click() -> pygame.mixer.Sound:
    return _montar_som(_gerar_onda(44100, 0.06,
        lambda i,n,sr: math.sin(2*math.pi*660*i/sr)*math.sin(math.pi*i/n)*0.25))

def _som_contador_go() -> pygame.mixer.Sound:
    """Beep de contagem regressiva GO!"""
    sr = 44100; buf = []
    for nota in [880, 1047]:
        n = int(sr*0.12)
        for i in range(n):
            onda = math.sin(2*math.pi*nota*i/sr) * math.sin(math.pi*i/n) * 0.5
            val  = max(-32768, min(32767, int(onda*32767)))
            buf += [val, val]
    return _montar_som(buf)


print(f"Pasta de áudios detectada: {SONS_DIR}")
print(f"  -> existe: {os.path.isdir(SONS_DIR)}")
if os.path.isdir(SONS_DIR):
    print(f"  -> arquivos encontrados: {os.listdir(SONS_DIR)}")
print("Carregando sons...")
SOM_COMER        = _carregar_som_arquivo("comer.mp3",        _som_comer)
SOM_MORTE        = _som_morte()
SOM_POWER        = _carregar_som_arquivo("maca_dourada.mp3", _som_power)
SOM_NIVEL        = _carregar_som_arquivo("subir_nivel.mp3",  _som_nivel)
SOM_BOTAO        = _carregar_som_arquivo("botao_menu.mp3",   lambda: _som_beep(880, 0.05, 0.2))
SOM_VOLTAR       = _carregar_som_arquivo("botao_menu.mp3",   lambda: _som_beep(440, 0.05, 0.15))
SOM_MULTI_PEGAR  = _carregar_som_arquivo("powerup_multi.mp3",_som_multi_powerup)
SOM_MULTI_FIM    = _som_multi_expirar()
SOM_EMBOSCADA    = _som_emboscada()
SOM_MOEDA        = _som_moeda()
SOM_DESBLOQUEIO  = _som_desbloqueio()

# Sons extras de contexto
print("Carregando sons de contexto...")
SOM_EXPLOSAO      = _som_explosao()
SOM_NIVEL_UP      = _carregar_som_arquivo("subir_nivel.mp3",  _som_nivel_up_especial)
SOM_POWERUP_PEGAR = _carregar_som_arquivo("powerup.mp3",      _som_powerup_especial)
SOM_TUTORIAL_CLICK = _som_tutorial_click()
SOM_GO            = _som_contador_go()
SOM_GAMEOVER      = _carregar_som_arquivo("gameover.mp3",     _gerar_musica_gameover)

# Instância global do gerenciador de música
MUSICA = MusicaFundo()
print("Sons carregados!")


# ================================================================
# HELPERS DE NÍVEL
# ================================================================
def nivel_para_pontos(pontos: int) -> int:
    nivel = 1
    for i, t in enumerate(THRESHOLDS_NIVEL):
        if pontos >= t: nivel = i + 1
        else: break
    return min(nivel, len(THRESHOLDS_NIVEL))

def proximo_threshold(pontos: int) -> Optional[int]:
    n = nivel_para_pontos(pontos)
    return THRESHOLDS_NIVEL[n] if n < len(THRESHOLDS_NIVEL) else None


# ================================================================
# PARTÍCULAS
# ================================================================
particulas: list = []

def adicionar_particulas(gx: int, gy: int, cor: tuple, qtd: int = 8) -> None:
    for _ in range(qtd):
        particulas.append({
            "x": gx*GRID+GRID//2, "y": gy*GRID+AREA_JOGO_Y+GRID//2,
            "vx": random.uniform(-3,3), "vy": random.uniform(-4,1),
            "vida": 30, "cor": cor, "tam": random.randint(2,5),
        })

def atualizar_particulas(dt: float = 1/60) -> None:
    escala = dt * 60
    for p in particulas[:]:
        p["x"] += p["vx"]*escala; p["y"] += p["vy"]*escala
        p["vy"] += 0.2*escala;    p["vida"] -= escala
        if p["vida"] <= 0: particulas.remove(p)

def desenhar_particulas() -> None:
    for p in particulas:
        pygame.draw.circle(tela, p["cor"], (int(p["x"]), int(p["y"])), p["tam"])


# ================================================================
# FLASH DE TELA
# ================================================================
flash_alpha: float = 0
flash_cor: tuple   = BRANCO

def flash(cor: tuple = BRANCO, intensidade: int = 120) -> None:
    global flash_alpha, flash_cor
    flash_alpha = intensidade; flash_cor = cor

def desenhar_flash() -> None:
    global flash_alpha
    if flash_alpha > 0:
        s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        s.fill((*flash_cor, int(flash_alpha))); tela.blit(s, (0,0))
        flash_alpha = max(0.0, flash_alpha - 8.0)


# ================================================================
# PRIMITIVAS CYBERPUNK
# ================================================================
def _painel_cyber(surf: pygame.Surface, rect: tuple,
                  cor_borda: tuple = CYBER_BORDA, alpha: int = 210,
                  borda: int = 2, raio: int = 8) -> None:
    """Desenha painel semitransparente com borda neon."""
    x, y, w, h = rect
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    bg.fill((*CYBER_PANEL, alpha))
    surf.blit(bg, (x, y))
    pygame.draw.rect(surf, cor_borda, (x, y, w, h), borda, border_radius=raio)

def _glow_text(surf: pygame.Surface, fonte: pygame.font.Font, texto: str,
               cor: tuple, pos: tuple, glow_cor: tuple = None,
               glow_r: int = 3, centro: bool = False) -> None:
    """Texto com efeito de brilho (glow) neon."""
    gc = glow_cor or tuple(min(255, c+60) for c in cor)
    rendered = fonte.render(texto, True, cor)
    gw, gh   = rendered.get_size()
    if centro:
        rx = pos[0] - gw//2; ry = pos[1] - gh//2
    else:
        rx, ry = pos

    # Camadas de glow
    for r in range(glow_r, 0, -1):
        g_surf = fonte.render(texto, True, gc)
        a      = max(0, int(80 * r / glow_r))
        g_surf.set_alpha(a)
        for ox, oy in [(-r,0),(r,0),(0,-r),(0,r),(-r,-r),(r,-r),(-r,r),(r,r)]:
            surf.blit(g_surf, (rx+ox, ry+oy))
    surf.blit(rendered, (rx, ry))

def _linha_scanline(surf: pygame.Surface, y: int, cor: tuple, alpha: int = 30) -> None:
    s = pygame.Surface((LARGURA, 1), pygame.SRCALPHA)
    s.fill((*cor, alpha)); surf.blit(s, (0, y))

def _rect_alpha(surf: pygame.Surface, cor: tuple, alpha: int, rect: tuple, raio: int = 0) -> None:
    """Desenha rect com alpha numa surface qualquer (inclusive tela principal)."""
    x, y, w, h = rect
    s = pygame.Surface((max(1,w), max(1,h)), pygame.SRCALPHA)
    r = tuple(int(c) for c in cor[:3])
    pygame.draw.rect(s, (*r, max(0, min(255, alpha))), (0, 0, max(1,w), max(1,h)), border_radius=raio)
    surf.blit(s, (x, y))

def _linha_alpha(surf: pygame.Surface, cor: tuple, alpha: int,
                 p1: tuple, p2: tuple, espessura: int = 1) -> None:
    """Desenha linha com alpha numa surface qualquer."""
    x1, y1 = p1; x2, y2 = p2
    w = max(1, abs(x2-x1)) if y1==y2 else espessura
    h = max(1, abs(y2-y1)) if x1==x2 else espessura
    bx, by = min(x1,x2), min(y1,y2)
    s = pygame.Surface((max(1,w), max(1,h)), pygame.SRCALPHA)
    r = tuple(int(c) for c in cor[:3])
    s.fill((*r, max(0, min(255, alpha))))
    surf.blit(s, (bx, by))

def _borda_alpha(surf: pygame.Surface, cor: tuple, alpha: int, espessura: int = 2) -> None:
    """Desenha borda ao redor da tela com alpha."""
    r = tuple(int(c) for c in cor[:3])
    a = max(0, min(255, alpha))
    for borda_surf, pos in [
        (pygame.Surface((LARGURA, espessura), pygame.SRCALPHA), (0, 0)),
        (pygame.Surface((LARGURA, espessura), pygame.SRCALPHA), (0, ALTURA-espessura)),
        (pygame.Surface((espessura, ALTURA),  pygame.SRCALPHA), (0, 0)),
        (pygame.Surface((espessura, ALTURA),  pygame.SRCALPHA), (LARGURA-espessura, 0)),
    ]:
        borda_surf.fill((*r, a))
        surf.blit(borda_surf, pos)

def _barra_progresso(surf: pygame.Surface, rect: tuple, progresso: float,
                     cor: tuple, cor_fundo: tuple = CINZA_ESC,
                     raio: int = 4) -> None:
    x, y, w, h = rect
    pygame.draw.rect(surf, cor_fundo, (x, y, w, h), border_radius=raio)
    fw = max(0, int(w * min(1.0, progresso)))
    if fw > 0:
        pygame.draw.rect(surf, cor, (x, y, fw, h), border_radius=raio)
        # brilho interno
        brilho = pygame.Surface((fw, h//2), pygame.SRCALPHA)
        brilho.fill((*cor, 60))
        surf.blit(brilho, (x, y))

def _desenhar_grid_cyber() -> None:
    for x in range(0, LARGURA, GRID):
        pygame.draw.line(tela, (12, 22, 12), (x, AREA_JOGO_Y), (x, ALTURA))
    for y in range(AREA_JOGO_Y, ALTURA, GRID):
        pygame.draw.line(tela, (12, 22, 12), (0, y), (LARGURA, y))


# ================================================================
# HUD IN-GAME
# ================================================================
# ================================================================
# SISTEMA UNIFICADO DE HUD — helpers internos
# ================================================================
def _hud_card(x: int, label: str, valor: str,
              cor_label: tuple, cor_valor: tuple,
              cor_borda: tuple, w: int = 180) -> None:
    """Desenha um card de stat na HUD com label em cima e valor embaixo."""
    h = AREA_JOGO_Y - 8
    _painel_cyber(tela, (x, 4, w, h), cor_borda=cor_borda, alpha=200, borda=1, raio=5)
    lbl = fonte_mini.render(label, True, cor_label)
    val = fonte_hud.render(valor, True, cor_valor)
    tela.blit(lbl, (x + w//2 - lbl.get_width()//2, 7))
    tela.blit(val, (x + w//2 - val.get_width()//2, 22))

def _hud_base(cor_fundo: tuple, cor_borda: tuple) -> None:
    """Desenha o fundo e borda inferior da HUD."""
    pygame.draw.rect(tela, cor_fundo, (0, 0, LARGURA, AREA_JOGO_Y))
    pygame.draw.line(tela, cor_borda, (0, AREA_JOGO_Y), (LARGURA, AREA_JOGO_Y), 2)
    # Varredura luminosa animada
    t = time.time()
    bx = int((t * 220) % LARGURA)
    sg = pygame.Surface((100, 2), pygame.SRCALPHA)
    sg.fill((*cor_borda, 100))
    tela.blit(sg, (bx - 50, AREA_JOGO_Y - 1))


def desenhar_hud(pontos: int, nivel: int, combo: int,
                 multiplicador: int, snake, multi_nivel: int = 1,
                 multi_pw_valor: int = 1, multi_pw_restante: float = 0.0,
                 moedas: int = 0) -> None:
    """HUD do modo CLÁSSICO — tema verde neon."""
    _hud_base((6, 14, 6), VERDE_NEO)

    # Cards alinhados uniformemente
    GAP = 8; x = GAP
    CARD_W = 186
    _hud_card(x, "PONTOS", f"{pontos:,}".replace(",","."), VERDE_NEO, BRANCO, VERDE_NEO, CARD_W); x += CARD_W + GAP
    _hud_card(x, "NÍVEL",  str(nivel),                    DOURADO,   DOURADO, DOURADO,   120);    x += 120 + GAP
    _hud_card(x, "COBRA",  str(len(snake.corpo)),         CIANO,     BRANCO,  CIANO,     120);    x += 120 + GAP
    _hud_card(x, "MOEDAS", str(moedas),                   DOURADO,   DOURADO, DOURADO,   140)

    # Combo e multiplicadores — lado direito
    rx = LARGURA - GAP
    if multi_pw_valor > 1 and multi_pw_restante > 0:
        cor_pw = MULTI_CORES.get(multi_pw_valor, CIANO)
        pw_w   = 170
        rx    -= pw_w + GAP
        _painel_cyber(tela, (rx, 4, pw_w, AREA_JOGO_Y-8), cor_borda=cor_pw, alpha=210, borda=2, raio=5)
        lbl = fonte_mini.render(f"×{multi_pw_valor} POWER", True, cor_pw)
        tela.blit(lbl, (rx + pw_w//2 - lbl.get_width()//2, 7))
        frac = max(0.0, min(1.0, multi_pw_restante / MULTI_DURACAO))
        bw = pw_w - 12
        pygame.draw.rect(tela, CINZA_ESC, (rx+6, 30, bw, 6), border_radius=3)
        pygame.draw.rect(tela, cor_pw,    (rx+6, 30, int(bw*frac), 6), border_radius=3)
        rx -= GAP

    if combo > 1:
        cor_combo = ROSA
        combo_w   = 140
        rx -= combo_w + GAP
        _painel_cyber(tela, (rx, 4, combo_w, AREA_JOGO_Y-8), cor_borda=cor_combo, alpha=210, borda=2, raio=5)
        lbl2 = fonte_mini.render("COMBO", True, cor_combo)
        val2 = fonte_hud.render(f"x{multiplicador}", True, cor_combo)
        tela.blit(lbl2, (rx + combo_w//2 - lbl2.get_width()//2, 7))
        tela.blit(val2, (rx + combo_w//2 - val2.get_width()//2, 22))


# ================================================================
# COBRA DO JOGADOR
# ================================================================
class Snake:
    def __init__(self, skin: str = "classico"):
        self.skin = skin
        self.reset()

    def reset(self) -> None:
        self.corpo:            list  = [(10,10),(9,10),(8,10)]
        self.direcao:          tuple = (1, 0)
        self.prox_direcao:     tuple = (1, 0)
        self.power:            bool  = False
        self.power_time:       float = 0
        self.shield:           bool  = False
        self.shield_time:      float = 0
        self.velocidade_boost: bool  = False
        self.boost_time:       float = 0
        self.pulso:            float = 0
        self.trail:            list  = []

    def mover(self) -> None:
        self.direcao = self.prox_direcao
        x, y = self.corpo[0]; dx, dy = self.direcao
        self.trail.append(self.corpo[0])
        if len(self.trail) > 6: self.trail.pop(0)
        self.corpo.insert(0, (x+dx, y+dy)); self.corpo.pop()

    def crescer(self) -> None:
        self.corpo.append(self.corpo[-1])

    def colisao(self) -> bool:
        if self.shield: return False
        x, y = self.corpo[0]
        if x < 0 or x >= COLUNAS or y < 0 or y >= LINHAS: return True
        return self.corpo[0] in self.corpo[1:]

    def _cor_segmento(self, i: int, pv: int) -> tuple:
        if self.power:
            return (255, max(180,min(255,220+pv)), max(0,pv-10))
        if self.shield:
            return (100, max(0,min(255,200+pv)), 255)
        paleta = PALETA_SKINS.get(self.skin)
        if paleta is None:  # arco-íris
            h = (i * 30 + time.time()*40) % 360
            return _hsv(h, 1.0, 1.0)
        # Tigre: alterna listras laranja/preto
        if self.skin == "tigre":
            if i % 2 == 0:
                return (min(255, 255 + pv//2), min(255, 140 + pv//2), 0)
            else:
                return (max(0, 50 + pv//3), max(0, 30 + pv//3), max(0, 30 + pv//3))
        # Cobra real: padrão escamado verde escuro/claro alternado
        if self.skin == "cobra_r":
            if i % 3 == 0:
                return (max(0, min(255, 20 + pv//2)), max(0, min(255, 180 + pv)), max(0, 20 + pv//3))
            else:
                return (max(0, min(255, 10 + pv//3)), max(0, min(255, 100 + pv//2)), max(0, 10 + pv//3))
        # Dragão: vermelho com brilho dourado nas bordas
        if self.skin == "dragao":
            if i % 4 == 0:
                return (min(255, 255), min(255, 120 + pv), max(0, pv - 20))
            else:
                return (min(255, 180 + pv//2), max(0, pv//2), max(0, pv//4))
        c1, c2 = paleta
        t = max(0.0, min(1.0, i / max(1, len(self.corpo))))
        return tuple(int(c1[k]*(1-t)+c2[k]*t) for k in range(3))

    def _desenhar_cabeca_animal(self, ex: int, ey: int) -> None:
        """Desenha detalhes especiais na cabeça para skins animais."""
        t_now = time.time()
        if self.skin == "leao":
            # Juba dourada ao redor da cabeça
            juba_cor = (220, 140, 0)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                jx = ex + GRID//2 + int(math.cos(rad) * (GRID//2 + 3))
                jy = ey + GRID//2 + int(math.sin(rad) * (GRID//2 + 3))
                pygame.draw.circle(tela, juba_cor, (jx, jy), 3)
        elif self.skin == "dragao":
            # Chifres no topo
            dx2, dy2 = self.direcao
            if dy2 == -1 or dy2 == 0:
                pygame.draw.polygon(tela, (255, 80, 0),
                    [(ex+4, ey+6), (ex+2, ey-4), (ex+8, ey+4)])
                pygame.draw.polygon(tela, (255, 80, 0),
                    [(ex+GRID-4, ey+6), (ex+GRID-2, ey-4), (ex+GRID-8, ey+4)])
        elif self.skin == "cobra_r":
            # Língua bifurcada
            dx2, dy2 = self.direcao
            tip_x = ex + GRID//2 + dx2*(GRID//2+4)
            tip_y = ey + GRID//2 + dy2*(GRID//2+4)
            fork = 4
            if abs(dx2) == 1:
                pygame.draw.line(tela, (220,30,30), (tip_x-dx2*3, tip_y), (tip_x, tip_y-fork), 2)
                pygame.draw.line(tela, (220,30,30), (tip_x-dx2*3, tip_y), (tip_x, tip_y+fork), 2)
            else:
                pygame.draw.line(tela, (220,30,30), (tip_x, tip_y-dy2*3), (tip_x-fork, tip_y), 2)
                pygame.draw.line(tela, (220,30,30), (tip_x, tip_y-dy2*3), (tip_x+fork, tip_y), 2)
        elif self.skin == "tigre":
            # Bigodes
            cx2 = ex + GRID//2; cy2 = ey + GRID//2
            pygame.draw.line(tela, (255,255,200), (cx2-2, cy2+2), (cx2-9, cy2-1), 2)
            pygame.draw.line(tela, (255,255,200), (cx2-2, cy2+2), (cx2-9, cy2+5), 2)
            pygame.draw.line(tela, (255,255,200), (cx2+2, cy2+2), (cx2+9, cy2-1), 2)
            pygame.draw.line(tela, (255,255,200), (cx2+2, cy2+2), (cx2+9, cy2+5), 2)

    def desenhar(self) -> None:
        self.pulso = (self.pulso + 0.2) % (2*math.pi)
        pv = int(math.sin(self.pulso)*20)
        corpo_set = set(self.corpo)

        for i, t in enumerate(self.trail):
            if t in corpo_set: continue
            a = int(60*((i+1)/len(self.trail)))
            cor_t = (max(0,a), max(0,a//2), 0) if self.power else (0,max(0,a),max(0,a//2))
            pygame.draw.rect(tela, cor_t,
                (t[0]*GRID+3, t[1]*GRID+AREA_JOGO_Y+3, GRID-6, GRID-6), border_radius=3)

        for i, p in enumerate(self.corpo):
            cor = self._cor_segmento(i, pv)
            pygame.draw.rect(tela, cor,
                (p[0]*GRID+1, p[1]*GRID+AREA_JOGO_Y+1, GRID-2, GRID-2), border_radius=4)
            # Detalhes extras skins animais no corpo
            if self.skin == "tigre" and i > 0 and i % 2 == 0:
                # Listra preta extra no centro do segmento
                pygame.draw.rect(tela, (20,20,20),
                    (p[0]*GRID+6, p[1]*GRID+AREA_JOGO_Y+6, GRID-12, GRID-12), border_radius=2)
            if i == 0:
                ex, ey = p[0]*GRID, p[1]*GRID+AREA_JOGO_Y
                dx, dy = self.direcao
                o1, o2 = int(GRID*0.72), int(GRID*0.22)
                if   dx ==  1: olhos = [(ex+o1,ey+o2),     (ex+o1,ey+GRID-o2)]
                elif dx == -1: olhos = [(ex+o2,ey+o2),     (ex+o2,ey+GRID-o2)]
                elif dy == -1: olhos = [(ex+o2,ey+o2),     (ex+GRID-o2,ey+o2)]
                else:          olhos = [(ex+o2,ey+o1),     (ex+GRID-o2,ey+o1)]
                # Olhos especiais por skin
                if self.skin == "leao":
                    for olho in olhos:
                        pygame.draw.circle(tela, (255,200,0), olho, 5)
                        pygame.draw.circle(tela, (80,40,0), olho, 3)
                elif self.skin == "dragao":
                    for olho in olhos:
                        pygame.draw.circle(tela, (255,80,0), olho, 5)
                        pygame.draw.circle(tela, (0,0,0), olho, 2)
                elif self.skin == "tigre":
                    for olho in olhos:
                        pygame.draw.circle(tela, (255,200,0), olho, 4)
                        pygame.draw.circle(tela, PRETO, olho, 2)
                else:
                    for olho in olhos:
                        pygame.draw.circle(tela, BRANCO, olho, 4)
                        pygame.draw.circle(tela, PRETO, olho, 2)
                # Detalhes extras na cabeça para animais
                if self.skin in SKIN_ANIMAL_TIPO:
                    self._desenhar_cabeca_animal(ex, ey)

        if self.shield:
            cx = self.corpo[0][0]*GRID+GRID//2; cy = self.corpo[0][1]*GRID+AREA_JOGO_Y+GRID//2
            pygame.draw.circle(tela, AZUL, (cx,cy), int(GRID*0.9+math.sin(self.pulso)*3), 2)

def _hsv(h: float, s: float, v: float) -> tuple:
    """Converte HSV (h=0-360) para RGB."""
    h = h % 360; i = int(h/60); f = h/60 - i
    p = v*(1-s); q = v*(1-f*s); t2 = v*(1-(1-f)*s)
    partes = [(v,t2,p),(q,v,p),(p,v,t2),(p,q,v),(t2,p,v),(v,p,q)]
    r, g, b = partes[i % 6]
    return (int(r*255), int(g*255), int(b*255))


# ================================================================
# IA — PERSONALIDADES
# ================================================================
class Personalidade(Enum):
    AGRESSIVA   = auto()
    DEFENSIVA   = auto()
    ESTRATEGICA = auto()
    EMBOSCADORA = auto()
    COOPERATIVA = auto()

@dataclass
class EstadoMemoria:
    historico_player:   list  = field(default_factory=list)
    posicao_emboscada:  Optional[tuple] = None
    tempo_emboscada:    float = 0.0
    cooldown_emboscada: float = 0.0
    alvo_cooperativo:   Optional[tuple] = None
    frustração:         int   = 0

class DificuldadeDinamica:
    def __init__(self):
        self.fator: float = 1.0; self.historico: list = []; self.janela: int = 120
    def registrar(self, pontos: int) -> None:
        self.historico.append(pontos)
        if len(self.historico) > self.janela: self.historico.pop(0)
    def atualizar(self) -> None:
        if len(self.historico) < 20: return
        crescimento = self.historico[-1] - self.historico[0]
        alvo = 0.6 + min(crescimento/100, 2.0)*0.45
        self.fator = max(0.4, min(1.8, self.fator*0.92 + alvo*0.08))
    def velocidade_extra(self) -> float: return max(0.0, self.fator-1.0)*0.5

dificuldade_din = DificuldadeDinamica()


# ================================================================
# COBRA INIMIGA
# ================================================================
class EnemySnake:
    CORES_PERSONALIDADE = {
        Personalidade.AGRESSIVA:   (255, 60, 60),
        Personalidade.DEFENSIVA:   (50, 180, 255),
        Personalidade.ESTRATEGICA: (170, 50, 255),
        Personalidade.EMBOSCADORA: (255, 140, 0),
        Personalidade.COOPERATIVA: (0, 200, 180),
    }

    def __init__(self, nivel_jogo: int = 1,
                 personalidade: Optional[Personalidade] = None, id_inimigo: int = 0):
        self.id            = id_inimigo
        self.nivel_jogo    = nivel_jogo
        self.personalidade = personalidade or random.choice(list(Personalidade))
        self.cor           = self.CORES_PERSONALIDADE[self.personalidade]
        self.cor_base      = self.cor
        self.direcao       = (1, 0)
        self.pulso         = random.uniform(0, math.pi*2)
        self.corpo: list   = []
        self.alvo_fixo     = None
        self.memoria_alvo  = 0
        self.power         = False
        self.power_time    = 0.0
        self.memoria       = EstadoMemoria()
        self._tick         = 0
        self._humor        = 0.5
        self._alvo_prev    = None
        self._ciclo_count  = 0
        self.spawn()

    def spawn(self, ocupados: set = None) -> None:
        ocupados = ocupados or set()
        for _ in range(100):
            cx, cy = random.randint(3,COLUNAS-4), random.randint(3,LINHAS-4)
            cands  = [(cx,cy),(cx-1,cy),(cx-2,cy)]
            if not any(p in ocupados for p in cands):
                self.corpo = cands; self.direcao = random.choice([(1,0),(-1,0),(0,1),(0,-1)]); return
        cx, cy = random.randint(3,COLUNAS-4), random.randint(3,LINHAS-4)
        self.corpo = [(cx,cy),(cx-1,cy),(cx-2,cy)]; self.direcao = random.choice([(1,0),(-1,0),(0,1),(0,-1)])

    def _espaco_livre(self, sx, sy, bloqueados, limite=80) -> int:
        visitados, fila = set(), [(sx,sy)]
        while fila and len(visitados) < limite:
            x, y = fila.pop()
            if (x,y) in visitados or (x,y) in bloqueados: continue
            if not (0<=x<COLUNAS and 0<=y<LINHAS): continue
            visitados.add((x,y))
            for d in [(1,0),(-1,0),(0,1),(0,-1)]: fila.append((x+d[0],y+d[1]))
        return len(visitados)

    def _candidatos_validos(self, bloqueados) -> list:
        x, y = self.corpo[0]; dx, dy = self.direcao
        todas = [(1,0),(-1,0),(0,1),(0,-1)]
        def ok(nx,ny): return (0<=nx<COLUNAS and 0<=ny<LINHAS
                               and (nx,ny) not in self.corpo[1:] and (nx,ny) not in bloqueados)
        sem_uturn = [(a,b) for a,b in todas if not (a==-dx and b==-dy)]
        validas   = [(a,b) for a,b in sem_uturn if ok(x+a,y+b)]
        return validas or [(a,b) for a,b in todas if ok(x+a,y+b)]

    def _astar_passo(self, sx, sy, tx, ty, bloqueados, limite=500) -> tuple:
        if (sx,sy)==(tx,ty): return 0, None
        aberto = []
        for a,b in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny=sx+a,sy+b
            if 0<=nx<COLUNAS and 0<=ny<LINHAS and (nx,ny) not in bloqueados:
                heapq.heappush(aberto,(1+abs(tx-nx)+abs(ty-ny),1,nx,ny,(a,b)))
        visitados = {(sx,sy)}
        while aberto:
            f,g,x,y,primeiro = heapq.heappop(aberto)
            if (x,y)==(tx,ty): return g, primeiro
            if (x,y) in visitados: continue
            visitados.add((x,y))
            if len(visitados)>limite: break
            for a,b in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx,ny=x+a,y+b
                if (nx,ny) not in visitados and 0<=nx<COLUNAS and 0<=ny<LINHAS and (nx,ny) not in bloqueados:
                    ng=g+1; heapq.heappush(aberto,(ng+abs(tx-nx)+abs(ty-ny),ng,nx,ny,primeiro))
        return 9999, None

    def _prever_jogador(self, historico, passos) -> tuple:
        if len(historico) < 3: return historico[-1] if historico else (COLUNAS//2,LINHAS//2)
        n = min(5,len(historico))
        dx_med=(historico[-1][0]-historico[-n][0])/n; dy_med=(historico[-1][1]-historico[-n][1])/n
        px,py=historico[-1]
        return (max(1,min(COLUNAS-2,int(px+dx_med*passos))),max(1,min(LINHAS-2,int(py+dy_med*passos))))

    def _alvo_fuga(self, player_pos, bloqueados) -> tuple:
        px,py=player_pos; melhor,melhor_score=None,-1
        for _ in range(40):
            cx=random.randint(1,COLUNAS-2); cy=random.randint(1,LINHAS-2)
            if (cx,cy) not in bloqueados:
                s=abs(cx-px)+abs(cy-py)+self._espaco_livre(cx,cy,bloqueados,30)
                if s>melhor_score: melhor_score,melhor=s,(cx,cy)
        return melhor or (COLUNAS//2,LINHAS//2)

    def _calcular_emboscada(self, player_pos, player_direcao, bloqueados) -> Optional[tuple]:
        agora=time.time()
        if agora < self.memoria.cooldown_emboscada: return self.memoria.posicao_emboscada
        x,y=self.corpo[0]; px,py=player_pos; dx,dy=player_direcao or (1,0)
        candidatos=[]; ppx,ppy=px,py
        for passos in range(3,14,2):
            ppx=max(0,min(COLUNAS-1,ppx+dx)); ppy=max(0,min(LINHAS-1,ppy+dy))
            if (ppx,ppy) not in bloqueados:
                db,_=self._astar_passo(x,y,ppx,ppy,bloqueados,300)
                dp=abs(px-ppx)+abs(py-ppy)
                if db<=dp+1 and db<9999: candidatos.append((ppx,ppy,dp-db))
        if not candidatos: return None
        melhor=max(candidatos,key=lambda c:c[2]); ponto=(melhor[0],melhor[1])
        self.memoria.posicao_emboscada=ponto; self.memoria.cooldown_emboscada=agora+4.0
        return ponto

    def _alvo_comida_prox(self, x, y, foods, bloqueados) -> tuple:
        if self.alvo_fixo and self.alvo_fixo in foods: return self.alvo_fixo
        melhor_d,melhor_f=9999,None
        for f in foods:
            d,_=self._astar_passo(x,y,f[0],f[1],bloqueados,150)
            if d<melhor_d: melhor_d,melhor_f=d,f
        alvo=melhor_f or (foods[0] if foods else (COLUNAS//2,LINHAS//2))
        self.alvo_fixo=alvo; return alvo

    def _atualizar_humor(self) -> None:
        self._tick+=1
        alvo=0.5+0.4*math.sin(self._tick*0.07+self.id*1.3)+random.uniform(-0.05,0.05)
        self._humor=max(0.0,min(1.0,self._humor*0.95+alvo*0.05))
        if self.alvo_fixo==self._alvo_prev: self._ciclo_count+=1
        else: self._ciclo_count=0; self._alvo_prev=self.alvo_fixo
        if self._ciclo_count>15: self.alvo_fixo=None; self.memoria_alvo=0; self._ciclo_count=0

    def mover(self, foods, player_pos, outros_corpos=None,
              player_direcao=None, player_power=False,
              dourada_pos=None, aliados=None) -> None:
        if not self.corpo: return
        agora=time.time()
        if self.power and agora>self.power_time:
            self.power=False
            self.cor=self.cor_base  # restaura a cor original da personalidade
        self._atualizar_humor()
        x,y=self.corpo[0]; dx,dy=self.direcao; self.pulso+=0.15
        self.memoria.historico_player.append(player_pos)
        if len(self.memoria.historico_player)>20: self.memoria.historico_player.pop(0)

        bloqueados=set(self.corpo[1:]); cabecas_inimigas=[]
        for outro in (outros_corpos or []):
            if not self.power: bloqueados.update(outro)
            if outro: cabecas_inimigas.append(outro[0])

        candidatos=self._candidatos_validos(bloqueados)
        if not candidatos:
            self.corpo.insert(0,(x+dx,y+dy)); self.corpo.pop(); return

        nivel=max(1,min(self.nivel_jogo,10))
        fator_dif=dificuldade_din.fator
        agressividade=min(1.0,(0.1+(nivel-1)*0.1)*fator_dif*(0.7+self._humor*0.6))
        dist_player=abs(player_pos[0]-x)+abs(player_pos[1]-y)
        em_fuga=player_power and not self.power and dist_player<14
        passos_prev=max(2,min(nivel+1,10))
        alvo=player_pos

        if self.power:
            alvo=player_pos
            for cab in cabecas_inimigas:
                if abs(cab[0]-x)+abs(cab[1]-y)<dist_player and abs(cab[0]-x)+abs(cab[1]-y)<10:
                    alvo=cab; break
            self.alvo_fixo=None; self.memoria_alvo=0
        elif em_fuga:
            alvo=self._alvo_fuga(player_pos,bloqueados); self.alvo_fixo=None; self.memoria_alvo=0
        elif dourada_pos and not self.power and nivel>=2:
            if abs(dourada_pos[0]-x)+abs(dourada_pos[1]-y)<25:
                alvo=dourada_pos; self.alvo_fixo=alvo; self.memoria_alvo=nivel*4

        if not self.power and not em_fuga and alvo==player_pos:
            if self.personalidade==Personalidade.AGRESSIVA:
                if nivel>=4 and player_direcao and dist_player<18:
                    alvo=self._prever_jogador(self.memoria.historico_player,passos_prev)
                elif dist_player<12 or random.random()<agressividade:
                    alvo=player_pos; self.memoria_alvo=nivel*2
                elif foods: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)
                self.alvo_fixo=alvo

            elif self.personalidade==Personalidade.DEFENSIVA:
                if dist_player>15: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)
                elif nivel>=7 and random.random()<agressividade*0.5: alvo=player_pos
                elif foods: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)
                self.alvo_fixo=alvo

            elif self.personalidade==Personalidade.ESTRATEGICA:
                if nivel>=5 and player_direcao:
                    alvo=self._prever_jogador(self.memoria.historico_player,passos_prev+2)
                elif foods: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)
                self.alvo_fixo=alvo

            elif self.personalidade==Personalidade.EMBOSCADORA:
                if nivel>=3 and player_direcao:
                    ponto=self._calcular_emboscada(player_pos,player_direcao,bloqueados)
                    if ponto and dist_player>8:
                        alvo=ponto; self.alvo_fixo=ponto; self.memoria_alvo=20
                    elif foods: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)
                elif foods: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)

            elif self.personalidade==Personalidade.COOPERATIVA:
                if aliados and nivel>=4 and dist_player<25:
                    quadrante=self.id%4
                    offs=[(0,-5),(0,5),(5,0),(-5,0)][quadrante]
                    ax=max(1,min(COLUNAS-2,player_pos[0]+offs[0]))
                    ay=max(1,min(LINHAS-2, player_pos[1]+offs[1]))
                    alvo=(ax,ay) if (ax,ay) not in bloqueados else player_pos
                    self.alvo_fixo=alvo
                elif foods: alvo=self._alvo_comida_prox(x,y,foods,bloqueados)

        _,passo_otimo=self._astar_passo(x,y,alvo[0],alvo[1],bloqueados)
        melhor_dir,melhor_score=None,-999999
        for a,b in candidatos:
            nx,ny=x+a,y+b
            espaco=self._espaco_livre(nx,ny,bloqueados|{(x,y)})
            pen_trap=600 if espaco<max(3,len(self.corpo)//2) else 0
            pen_bord=(30 if nx in(0,COLUNAS-1) or ny in(0,LINHAS-1) else
                      12 if nx<=1 or nx>=COLUNAS-2 or ny<=1 or ny>=LINHAS-2 else 0)
            pen_cab=0 if self.power else sum(
                500 if abs(nx-cx)+abs(ny-cy)==0 else 180 if abs(nx-cx)+abs(ny-cy)==1 else
                50  if abs(nx-cx)+abs(ny-cy)==2 else 0 for cx,cy in cabecas_inimigas)
            if em_fuga:
                score=(espaco*3.5+(abs(player_pos[0]-nx)+abs(player_pos[1]-ny))*7
                       -pen_bord-pen_cab-pen_trap)
            else:
                bon=250*(agressividade if not self.power else 2.0) if (a,b)==passo_otimo else 0
                dc,_=self._astar_passo(nx,ny,alvo[0],alvo[1],bloqueados|{(x,y)},250)
                score=(espaco*2.0+bon-dc*4.0-pen_bord-pen_cab-pen_trap)
            ruido=max(0.1,2.0*(1.0-nivel*0.06))
            score+=random.uniform(-ruido,ruido)
            if score>melhor_score: melhor_score,melhor_dir=score,(a,b)

        # Hesitação humana em níveis baixos
        if melhor_dir and len(candidatos)>1 and random.random()<max(0.0,0.25-nivel*0.02):
            alts=[c for c in candidatos if c!=melhor_dir]
            if alts: melhor_dir=random.choice(alts)

        if melhor_dir: self.direcao=melhor_dir
        nova=(x+self.direcao[0],y+self.direcao[1]); self.corpo.insert(0,nova)
        if nova in foods:
            foods.remove(nova); self.alvo_fixo=None
            ocupados_comida=set(self.corpo)|set(foods)
            for _ in range(200):
                nc=(random.randrange(1,COLUNAS-1),random.randrange(1,LINHAS-1))
                if nc not in ocupados_comida: foods.append(nc); break
        else: self.corpo.pop()

    def desenhar(self) -> None:
        self.pulso=(self.pulso+0.15)%(2*math.pi); pv=int(math.sin(self.pulso)*25); r,g,b=self.cor
        for i,p in enumerate(self.corpo):
            if not (0<=p[0]<COLUNAS and 0<=p[1]<LINHAS): continue
            f=max(0.35,1.0-i*0.06)
            if self.power:
                pv2=int(abs(math.sin(self.pulso*2))*255)
                cor=(255,max(80,min(255,140+pv2//2)),0) if i==0 else (max(180,min(255,200+pv)),max(80,min(160,100+pv//2)),0)
            else:
                cor=(max(0,min(255,int(r*f)+pv)),max(0,min(255,int(g*f)+pv)),max(0,min(255,int(b*f)+pv))) if i==0 \
                    else (max(0,int(r*f)),max(0,int(g*f)),max(0,int(b*f)))
            pygame.draw.rect(tela,cor,(p[0]*GRID+1,p[1]*GRID+AREA_JOGO_Y+1,GRID-2,GRID-2),border_radius=4)
            if i==0:
                ex,ey=p[0]*GRID,p[1]*GRID+AREA_JOGO_Y; a,bb=self.direcao
                o1,o2=int(GRID*0.72),int(GRID*0.22)
                if   a== 1: olhos=[(ex+o1,ey+o2),(ex+o1,ey+GRID-o2)]
                elif a==-1: olhos=[(ex+o2,ey+o2),(ex+o2,ey+GRID-o2)]
                elif bb==-1:olhos=[(ex+o2,ey+o2),(ex+GRID-o2,ey+o2)]
                else:        olhos=[(ex+o2,ey+o1),(ex+GRID-o2,ey+o1)]
                cor_olho=DOURADO if self.power else BRANCO
                for olho in olhos:
                    pygame.draw.circle(tela,cor_olho,olho,4); pygame.draw.circle(tela,PRETO,olho,2)
                if self.power:
                    cx2=p[0]*GRID+GRID//2; cy2=p[1]*GRID+AREA_JOGO_Y+GRID//2
                    pygame.draw.circle(tela,DOURADO,(cx2,cy2),int(GRID*0.85+math.sin(self.pulso)*3),2)
                # barra indicador personalidade
                pygame.draw.rect(tela,self.cor,(p[0]*GRID+2,p[1]*GRID+AREA_JOGO_Y-3,GRID-4,2),border_radius=1)


# ================================================================
# SPAWN DE INIMIGOS POR NÍVEL
# ================================================================
def _personalidades_nivel(nivel: int) -> list:
    tabela = {
        1:  [Personalidade.AGRESSIVA],
        2:  [Personalidade.AGRESSIVA, Personalidade.DEFENSIVA],
        3:  [Personalidade.AGRESSIVA, Personalidade.DEFENSIVA, Personalidade.ESTRATEGICA],
        4:  [Personalidade.AGRESSIVA, Personalidade.EMBOSCADORA, Personalidade.DEFENSIVA],
        5:  [Personalidade.AGRESSIVA, Personalidade.EMBOSCADORA, Personalidade.ESTRATEGICA, Personalidade.COOPERATIVA],
        6:  [Personalidade.AGRESSIVA, Personalidade.ESTRATEGICA, Personalidade.EMBOSCADORA, Personalidade.COOPERATIVA, Personalidade.DEFENSIVA],
        7:  [Personalidade.AGRESSIVA]*2 + [Personalidade.EMBOSCADORA, Personalidade.COOPERATIVA, Personalidade.ESTRATEGICA, Personalidade.DEFENSIVA],
        8:  [Personalidade.AGRESSIVA]*2 + [Personalidade.EMBOSCADORA, Personalidade.COOPERATIVA, Personalidade.ESTRATEGICA, Personalidade.DEFENSIVA, Personalidade.AGRESSIVA],
        9:  [Personalidade.AGRESSIVA]*2 + [Personalidade.EMBOSCADORA]*2 + [Personalidade.COOPERATIVA, Personalidade.ESTRATEGICA, Personalidade.DEFENSIVA, Personalidade.AGRESSIVA],
        10: list(Personalidade)*2,
    }
    return tabela.get(nivel, tabela[10])[:nivel]

def criar_inimigos(nivel: int, snake_corpo: list) -> list:
    personalidades = _personalidades_nivel(nivel)
    inimigos = []; ocupados = set(snake_corpo)
    for i, pers in enumerate(personalidades):
        bot = EnemySnake(nivel_jogo=nivel, personalidade=pers, id_inimigo=i)
        bot.spawn(ocupados); inimigos.append(bot); ocupados.update(bot.corpo)
    return inimigos


# ================================================================
# COMIDAS
# ================================================================
class Foods:
    def __init__(self):
        self.normais: list = []; self.dourada: Optional[tuple] = None
        self.multi_pw: Optional[tuple] = None; self.gerar()

    def gerar(self) -> None:
        self.normais = [(random.randrange(1,COLUNAS-1), random.randrange(1,LINHAS-1)) for _ in range(3)]
        if random.random() < 0.4:
            self.dourada = (random.randrange(1,COLUNAS-1), random.randrange(1,LINHAS-1))

    def ajustar_macas_nivel(self, nivel: int, excluir: set = None) -> None:
        """Ajusta a quantidade de macas de acordo com o nivel (3 no nivel 1, +1 a cada nivel)."""
        alvo = min(2 + nivel, 12)  # nivel 1->3, nivel 2->4, ..., nivel 10->12
        excluir = set(excluir or []) | set(self.normais)
        while len(self.normais) < alvo:
            pos = self.nova_comida(excluir)
            self.normais.append(pos)
            excluir.add(pos)

    def nova_comida(self, excluir: set = None) -> tuple:
        excluir = set(excluir or [])
        for _ in range(50):
            pos = (random.randrange(1,COLUNAS-1), random.randrange(1,LINHAS-1))
            if pos not in excluir: return pos
        return (random.randrange(1,COLUNAS-1), random.randrange(1,LINHAS-1))

    def tentar_spawn_multi(self, excluir: set = None) -> None:
        if self.multi_pw is not None: return
        if random.random() < MULTI_CHANCE:
            excluir = set(excluir or []); valor = random.choice(MULTI_POWERUPS)
            for _ in range(50):
                pos=(random.randrange(2,COLUNAS-2),random.randrange(2,LINHAS-2))
                if pos not in excluir: self.multi_pw=(pos,valor); return

    def desenhar(self) -> None:
        t=time.time()
        for f in self.normais:
            tela.blit(SPRITE_MACA,(f[0]*GRID+1,f[1]*GRID+AREA_JOGO_Y+1))
        if self.dourada:
            pulso=0.85+0.15*abs(math.sin(t*4)); tam=int((GRID-2)*pulso)
            offset=(GRID-2-tam)//2
            scaled=pygame.transform.smoothscale(SPRITE_DOURADA,(tam,tam))
            tela.blit(scaled,(self.dourada[0]*GRID+1+offset,self.dourada[1]*GRID+AREA_JOGO_Y+1+offset))
        if self.multi_pw:
            pos,valor=self.multi_pw; cor=MULTI_CORES.get(valor,CIANO); pulso=abs(math.sin(t*5))
            cx=pos[0]*GRID+GRID//2; cy=pos[1]*GRID+AREA_JOGO_Y+GRID//2; raio=int(GRID*(0.38+0.10*pulso))
            aura=pygame.Surface((GRID*2,GRID*2),pygame.SRCALPHA)
            pygame.draw.circle(aura,(*cor,int(60+40*pulso)),(GRID,GRID),raio+5)
            tela.blit(aura,(cx-GRID,cy-GRID))
            pts=[(cx,cy-raio),(cx+raio,cy),(cx,cy+raio),(cx-raio,cy)]
            pygame.draw.polygon(tela,cor,pts); pygame.draw.polygon(tela,BRANCO,pts,2)
            label=fonte_peq.render(f"×{valor}",True,PRETO)
            tela.blit(label,(cx-label.get_width()//2,cy-label.get_height()//2))


# ================================================================
# INTRO DE VÍDEO
# ================================================================
def intro_video(caminho: str) -> None:
    try:
        import cv2, numpy as np
    except ImportError: return
    if not os.path.exists(caminho): return
    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened(): return
    fps_v = cap.get(cv2.CAP_PROP_FPS) or 24.0
    while True:
        ret, frame = cap.read()
        if not ret: break
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: cap.release(); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE,pygame.K_RETURN,pygame.K_SPACE):
                cap.release(); return
        surf = pygame.surfarray.make_surface(
            np.transpose(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB),(1,0,2)))
        tela.blit(pygame.transform.scale(surf,(LARGURA,ALTURA)),(0,0))
        hint=fonte_peq.render("ENTER / ESC para pular",True,(200,200,200))
        tela.blit(hint,(LARGURA//2-hint.get_width()//2,ALTURA-26))
        pygame.display.update(); clock.tick(fps_v)
    cap.release()


# ================================================================
# ANIMAÇÃO DE LEVEL UP
# ================================================================
def animacao_level_up(nivel: int, personalidades: list = None) -> None:
    """Animação de level up — card cyberpunk centralizado com lista de inimigos."""
    NOMES_PERS = {
        Personalidade.AGRESSIVA:   ("AGRESSIVA",   VERMELHO),
        Personalidade.DEFENSIVA:   ("DEFENSIVA",   AZUL),
        Personalidade.ESTRATEGICA: ("ESTRATEGICA", ROXO),
        Personalidade.EMBOSCADORA: ("EMBOSCADORA", LARANJA),
        Personalidade.COOPERATIVA: ("COOPERATIVA", TEAL),
    }
    DURACAO = 2.0
    inicio  = time.time()

    # Pré-renderiza os labels de personalidade
    pers_surfs: list = []
    if personalidades:
        for p in personalidades:
            nome, cor = NOMES_PERS.get(p, ("?", BRANCO))
            pers_surfs.append((fonte_mini.render(f"▸ {nome}", True, cor), cor))

    while True:
        elapsed = time.time() - inicio
        if elapsed >= DURACAO: break
        t = elapsed / DURACAO          # 0 → 1
        pulse = abs(math.sin(elapsed * 6))
        fade_out = max(0.0, 1.0 - t * 1.4)

        # Overlay escuro semi-transparente sobre o jogo
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(170 * fade_out)))
        tela.blit(overlay, (0, 0))

        # Card central
        cw = 460; ch = 200 + len(pers_surfs) * 26
        cx = LARGURA//2 - cw//2
        cy = ALTURA//2  - ch//2 - 20
        cor_card = tuple(min(255, int(VERDE_NEO[k] * (0.6 + pulse * 0.4))) for k in range(3))
        _painel_cyber(tela, (cx, cy, cw, ch), cor_borda=cor_card, alpha=int(230*fade_out), borda=3, raio=12)

        # Título NÍVEL
        escala = 1.0 + 0.08 * math.sin(elapsed * 8)
        txt = fonte_grande.render(f"NÍVEL  {nivel}", True, cor_card)
        stxt = pygame.transform.scale(txt, (int(txt.get_width()*escala), int(txt.get_height()*escala)))
        stxt.set_alpha(int(255 * fade_out))
        tela.blit(stxt, (LARGURA//2 - stxt.get_width()//2, cy + 16))

        # Linha separadora
        pygame.draw.line(tela, cor_card, (cx+20, cy+86), (cx+cw-20, cy+86), 1)

        # Sub-título
        sub = fonte_peq.render("NOVOS INIMIGOS", True, CYBER_DIM)
        sub.set_alpha(int(200 * fade_out))
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, cy + 94))

        # Lista de personalidades
        for i, (s, cor) in enumerate(pers_surfs):
            s2 = s.copy(); s2.set_alpha(int(240 * fade_out))
            tela.blit(s2, (LARGURA//2 - s.get_width()//2, cy + 118 + i * 26))

        pygame.display.update(); clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return


# ================================================================
# FUNDO CYBERPUNK ANIMADO (menu / ranking / stats)
# ================================================================
class FundoCyber:
    """Grid animado com partículas flutuantes para telas de UI."""
    def __init__(self):
        self.particulas = []
        self.t = 0.0
        for _ in range(25):
            self.particulas.append({
                "x": random.uniform(0, LARGURA), "y": random.uniform(0, ALTURA),
                "vy": random.uniform(0.3, 1.2), "vx": random.uniform(-0.3, 0.3),
                "r": random.randint(1, 3),
                "cor": random.choice([VERDE_NEO, CIANO, ROXO_BRILHO, MAGENTA]),
                "alpha": random.randint(40, 140),
            })

    def atualizar(self) -> None:
        self.t += 0.016
        for p in self.particulas:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] > ALTURA: p["y"] = -4; p["x"] = random.uniform(0, LARGURA)

    def desenhar(self) -> None:
        # Fundo escuro
        tela.fill(CYBER_BG)
        # Grid ciano fraco
        alpha_grid = 20
        for x in range(0, LARGURA, 60):
            s = pygame.Surface((1, ALTURA), pygame.SRCALPHA)
            s.fill((*CYBER_BORDA, alpha_grid)); tela.blit(s, (x, 0))
        for y in range(0, ALTURA, 60):
            s = pygame.Surface((LARGURA, 1), pygame.SRCALPHA)
            s.fill((*CYBER_BORDA, alpha_grid)); tela.blit(s, (0, y))

        # Partículas flutuantes
        for p in self.particulas:
            s = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["cor"], p["alpha"]), (p["r"], p["r"]), p["r"])
            tela.blit(s, (int(p["x"])-p["r"], int(p["y"])-p["r"]))

        # Linha scanline animada
        sy = int((self.t * 80) % ALTURA)
        sl = pygame.Surface((LARGURA, 2), pygame.SRCALPHA)
        sl.fill((*CIANO, 18)); tela.blit(sl, (0, sy))

        # Pulso de borda
        pulse = int(abs(math.sin(self.t*1.5)) * 60)
        _borda_alpha(tela, CYBER_BORDA, max(30, pulse))


_fundo_cyber = FundoCyber()

# ================================================================
# FUNDO CYBERPUNK ANIMADO — VERSÃO APRIMORADA
# ================================================================
class FundoCyber:
    """Grid animado com múltiplas camadas de efeitos para UI."""
    def __init__(self):
        self.particulas = []
        self.raios      = []   # raios de expansão (pulso)
        self.t          = 0.0
        self.estrelas   = []
        for _ in range(35):
            self.particulas.append({
                "x": random.uniform(0, LARGURA), "y": random.uniform(0, ALTURA),
                "vy": random.uniform(0.4, 1.5),  "vx": random.uniform(-0.4, 0.4),
                "r":  random.randint(1, 3),
                "cor": random.choice([VERDE_NEO, CIANO, ROXO_BRILHO, MAGENTA, DOURADO]),
                "alpha": random.randint(50, 160),
            })
        for _ in range(60):
            self.estrelas.append({
                "x": random.uniform(0, LARGURA), "y": random.uniform(0, ALTURA),
                "brilho": random.uniform(0.3, 1.0),
                "fase":   random.uniform(0, math.pi*2),
                "vel":    random.uniform(0.02, 0.08),
            })

    def _spawn_raio(self):
        if random.random() < 0.008:
            self.raios.append({
                "x": random.uniform(0, LARGURA), "y": random.uniform(0, ALTURA),
                "r": 0, "max_r": random.randint(60, 160),
                "cor": random.choice([CIANO, VERDE_NEO, MAGENTA]),
                "alpha": 200,
            })

    def atualizar(self) -> None:
        self.t += 0.016
        for p in self.particulas:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] > ALTURA:
                p["y"] = -4; p["x"] = random.uniform(0, LARGURA)
            if p["x"] < 0 or p["x"] > LARGURA:
                p["vx"] *= -1
        for e in self.estrelas:
            e["fase"] += e["vel"]
        self._spawn_raio()
        for raio in self.raios[:]:
            raio["r"]     += 2.5
            raio["alpha"] -= 6
            if raio["r"] >= raio["max_r"] or raio["alpha"] <= 0:
                self.raios.remove(raio)

    def desenhar(self) -> None:
        tela.fill(CYBER_BG)

        # Estrelas piscantes no fundo
        for e in self.estrelas:
            b = int(abs(math.sin(e["fase"])) * e["brilho"] * 80)
            if b > 10:
                s = pygame.Surface((2, 2), pygame.SRCALPHA)
                s.fill((min(255, b*2), min(255, b*3), min(255, b*4), min(255, b)))
                tela.blit(s, (int(e["x"]), int(e["y"])))

        # Grid com perspectiva leve
        for x in range(0, LARGURA, 60):
            alpha = int(12 + 8 * abs(math.sin(self.t * 0.5 + x * 0.01)))
            s = pygame.Surface((1, ALTURA), pygame.SRCALPHA)
            s.fill((*CYBER_BORDA, alpha)); tela.blit(s, (x, 0))
        for y in range(0, ALTURA, 60):
            alpha = int(12 + 8 * abs(math.sin(self.t * 0.5 + y * 0.01)))
            s = pygame.Surface((LARGURA, 1), pygame.SRCALPHA)
            s.fill((*CYBER_BORDA, alpha)); tela.blit(s, (0, y))

        # Raios de expansão (pulsos)
        for raio in self.raios:
            surf_r = pygame.Surface((raio["r"]*2+4, raio["r"]*2+4), pygame.SRCALPHA)
            pygame.draw.circle(surf_r, (*raio["cor"], max(0, int(raio["alpha"]))),
                               (raio["r"]+2, raio["r"]+2), int(raio["r"]), 1)
            tela.blit(surf_r, (int(raio["x"]) - raio["r"] - 2, int(raio["y"]) - raio["r"] - 2))

        # Partículas flutuantes com trail
        for p in self.particulas:
            s = pygame.Surface((p["r"]*2+2, p["r"]*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["cor"], p["alpha"]), (p["r"]+1, p["r"]+1), p["r"])
            tela.blit(s, (int(p["x"])-p["r"], int(p["y"])-p["r"]))

        # Scanline animada dupla
        sy  = int((self.t * 90) % ALTURA)
        sy2 = int((self.t * 55 + ALTURA/2) % ALTURA)
        for scan_y, alpha_s in [(sy, 22), (sy2, 12)]:
            sl = pygame.Surface((LARGURA, 2), pygame.SRCALPHA)
            sl.fill((*CIANO, alpha_s)); tela.blit(sl, (0, scan_y))

        # Borda pulsante com gradiente
        pulse = int(abs(math.sin(self.t * 1.8)) * 70 + 30)
        _borda_alpha(tela, CYBER_BORDA, max(20, pulse))
        # Cantos decorativos
        tam_canto = 20
        for cx2, cy2 in [(0,0),(LARGURA-tam_canto,0),(0,ALTURA-tam_canto),(LARGURA-tam_canto,ALTURA-tam_canto)]:
            pygame.draw.rect(tela, VERDE_NEO, (cx2, cy2, tam_canto, 2))
            pygame.draw.rect(tela, VERDE_NEO, (cx2, cy2, 2, tam_canto))


_fundo_cyber = FundoCyber()


# ================================================================
# TELA DE RANKING — TOP 10 APRIMORADO
# ================================================================
def tela_ranking(dados: dict) -> None:
    t         = 0.0
    medalhas  = ["1.", "2.", "3."]
    cores_pos = [DOURADO, (200,200,210), (200,120,50)]
    anim_in   = 0.0

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.02; anim_in = min(1.0, anim_in + 0.06)
        slide = int((1.0 - anim_in) * -80 * (1.0 - anim_in))

        # ── Título padrão ────────────────────────────────────────
        TITULO_Y = 46
        pulse_t = abs(math.sin(t * 2.5))
        cor_titulo = tuple(int(CIANO[k] * (0.8 + pulse_t * 0.2)) for k in range(3))
        _glow_text(tela, fonte_titulo, "RANKING", cor_titulo,
                   (LARGURA//2, TITULO_Y + slide), centro=True, glow_r=5)
        sub = fonte_peq.render("TOP 10 PONTUACOES GLOBAIS", True, CYBER_DIM)
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, TITULO_Y + 72 + slide))

        ranking = dados.get("ranking", [])

        # ── Painel principal ────────────────────────────────────
        PAINEL_Y = TITULO_Y + 106
        pw = LARGURA - 120
        ph = min(500, 60 + max(1, len(ranking)) * 48 + 16)
        px = LARGURA//2 - pw//2
        py = PAINEL_Y + slide
        _painel_cyber(tela, (px, py, pw, ph), cor_borda=CYBER_BORDA, alpha=220, borda=2, raio=10)

        # Cabeçalho proporcional à largura do painel
        col_x = {"pos": px+20, "pts": px+120, "lvl": px+310, "cobra": px+430,
                  "data": px+560, "dur": px+760}
        for txt, ox in [("#", col_x["pos"]), ("PONTUACAO", col_x["pts"]),
                        ("NIVEL", col_x["lvl"]), ("COBRA", col_x["cobra"]),
                        ("DATA", col_x["data"]), ("DURACAO", col_x["dur"])]:
            tela.blit(fonte_mini.render(txt, True, CYBER_DIM), (ox, py+12))

        pygame.draw.line(tela, CYBER_BORDA, (px+10, py+32), (px+pw-10, py+32), 1)

        if not ranking:
            s = fonte_med.render("Sem partidas registradas ainda", True, CINZA)
            tela.blit(s, (LARGURA//2 - s.get_width()//2, py + ph//2 - 20))
        else:
            for i, entrada in enumerate(ranking):
                ry    = py + 44 + i*46
                pulso = abs(math.sin(t*2.5 + i*0.6))
                if i < 3:
                    hl = pygame.Surface((pw-20, 40), pygame.SRCALPHA)
                    hl.fill((*cores_pos[i], int(18 + pulso*22)))
                    tela.blit(hl, (px+10, ry-1))
                    pygame.draw.rect(tela, cores_pos[i], (px+8, ry, 3, 36), border_radius=1)
                cor_txt = cores_pos[i] if i < 3 else CYBER_TEXTO
                pos_txt = (medalhas[i] if i < 3 else f"{i+1}.")
                tela.blit(fonte_ranking.render(pos_txt, True, cor_txt), (col_x["pos"], ry+4))
                pts_str = f"{entrada['pontos']:,}".replace(",", ".")
                if i == 0:
                    _glow_text(tela, fonte_ranking, pts_str, DOURADO, (col_x["pts"], ry+4), glow_r=3)
                else:
                    tela.blit(fonte_ranking.render(pts_str, True, cor_txt), (col_x["pts"], ry+4))
                tela.blit(fonte_ranking.render(f"Lvl {entrada['nivel']}", True, VERDE_NEO), (col_x["lvl"], ry+4))
                tela.blit(fonte_stat.render(str(entrada.get("cobra","—")), True, CYBER_DIM), (col_x["cobra"], ry+7))
                tela.blit(fonte_stat.render(entrada.get("data","—"), True, CYBER_DIM), (col_x["data"], ry+7))
                tela.blit(fonte_stat.render(_fmt_tempo(entrada.get("duracao",0)), True, CYBER_DIM), (col_x["dur"], ry+7))

        # ── Rodapé padrão ────────────────────────────────────────
        RODAPE_Y = ALTURA - 44
        mc = fonte_peq.render(f"{dados['moedas']} moedas     Skins: {len(dados['skins_desbloqueadas'])}/{len(SKINS_CUSTO)}", True, DOURADO)
        tela.blit(mc, (LARGURA//2 - mc.get_width()//2, RODAPE_Y - 18))
        _glow_text(tela, fonte_mini, "ESC  VOLTAR", CYBER_DIM, (LARGURA//2, RODAPE_Y + 4), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:   pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    SOM_VOLTAR.play(); return


# ================================================================
# TELA DE ESTATÍSTICAS — APRIMORADA
# ================================================================
def tela_estatisticas(dados: dict) -> None:
    t      = 0.0
    s      = dados["stats"]
    moedas = dados["moedas"]
    anim_in = 0.0

    total_s  = int(s["tempo_total_s"])
    partidas = max(1, s["partidas_jogadas"])
    media_s  = total_s // partidas

    kpis = [
        ("RECORDE",   f"{s['pontuacao_maxima']:,}".replace(",","."), DOURADO),
        ("NIVEL MAX", f"{s['nivel_maximo']}/10",                     VERDE_NEO),
        ("PARTIDAS",  str(s["partidas_jogadas"]),                    AZUL),
        ("MOEDAS",    str(moedas),                                   DOURADO),
    ]

    grupos = [
        ("COMBATE", [
            ("Mortes",               str(s["mortes"])),
            ("Inimigos eliminados",  str(s["inimigos_mortos"])),
            ("Combo maximo",         f"x{s['combo_maximo']}"),
            ("Power-ups coletados",  str(s["power_ups_coletados"])),
        ]),
        ("COLETA", [
            ("Macas comidas",        str(s["macas_comidas"])),
            ("Macas douradas",       str(s["macas_douradas"])),
            ("Macas por partida",    f"{s['macas_comidas']//partidas}"),
        ]),
        ("TEMPO", [
            ("Tempo total jogado",   _fmt_tempo(total_s)),
            ("Media por partida",    _fmt_tempo(media_s)),
            ("Partida mais longa",   _fmt_tempo(dados.get("partida_mais_longa_s", 0))),
        ]),
        ("SKINS", [
            ("Desbloqueadas",        f"{len(dados['skins_desbloqueadas'])}/{len(SKINS_CUSTO)}"),
            ("Skin ativa",           NOMES_SKINS.get(dados.get("skin_ativa","classico"),"?")),
        ]),
    ]

    TITULO_Y  = 46
    MARGEM_KPI = 36          # margem lateral dos KPIs
    KPI_GAP   = 14           # espaço entre cards KPI
    KPI_H     = 84
    n_kpi     = len(kpis)
    KPI_W     = (LARGURA - MARGEM_KPI*2 - KPI_GAP*(n_kpi-1)) // n_kpi
    KPI_Y     = TITULO_Y + 100
    GRID_Y    = KPI_Y + KPI_H + 18
    MARGEM_GRID = 36
    GRID_GAP  = 14
    COL_W     = (LARGURA - MARGEM_GRID*2 - GRID_GAP) // 2
    COL_H     = 196
    GRID_X0   = MARGEM_GRID
    CORES_G   = [VERMELHO, VERDE_NEO, CIANO, ROXO_BRILHO]

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.02; anim_in = min(1.0, anim_in + 0.07)
        slide = int((1.0 - anim_in) * -60 * (1.0 - anim_in))

        # ── Título padrão ────────────────────────────────────────
        pulse_t = abs(math.sin(t * 2.2))
        cor_m = tuple(int(MAGENTA[k] * (0.7 + pulse_t * 0.3)) for k in range(3))
        _glow_text(tela, fonte_titulo, "ESTATISTICAS", cor_m,
                   (LARGURA//2, TITULO_Y + slide), centro=True, glow_r=5, glow_cor=ROXO_BRILHO)
        sub = fonte_peq.render("HISTORICO COMPLETO DE PARTIDAS", True, CYBER_DIM)
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, TITULO_Y + 72 + slide))

        # ── KPIs em linha ────────────────────────────────────────
        kpi_y  = KPI_Y + slide

        for ki, (label, valor, cor_k) in enumerate(kpis):
            kx = MARGEM_KPI + ki * (KPI_W + KPI_GAP)
            pulse_k = abs(math.sin(t*2.5 + ki*0.8))
            _painel_cyber(tela, (kx, kpi_y, KPI_W, KPI_H),
                          cor_borda=cor_k, alpha=230, borda=2, raio=10)
            lb = fonte_mini.render(label, True, CYBER_DIM)
            tela.blit(lb, (kx+14, kpi_y+10))
            vl = fonte_grande.render(valor, True, cor_k)
            if vl.get_width() > KPI_W - 24:
                vl = fonte_med.render(valor, True, cor_k)
            tela.blit(vl, (kx + KPI_W//2 - vl.get_width()//2, kpi_y + KPI_H//2 - vl.get_height()//2 + 8))
            ul_w = int((KPI_W-28) * (0.7 + pulse_k*0.3))
            _rect_alpha(tela, cor_k, 80, (kx+14, kpi_y+KPI_H-5, ul_w, 3))

        # ── Grid 2×2 de grupos ───────────────────────────────────
        gy_base = GRID_Y + slide
        for idx, (titulo_g, linhas) in enumerate(grupos):
            col_i = idx % 2; row_i = idx // 2
            gx = GRID_X0 + col_i * (COL_W + GRID_GAP)
            gy = gy_base + row_i * (COL_H + GRID_GAP + 4)
            cor_g = CORES_G[idx]
            pulse_g = abs(math.sin(t*2 + idx*0.7))

            _painel_cyber(tela, (gx, gy, COL_W, COL_H),
                          cor_borda=cor_g, alpha=215, borda=2, raio=8)
            cor_tit = tuple(min(255, int(c*(0.75 + pulse_g*0.25))) for c in cor_g)
            titulo_surf = fonte_hud.render(titulo_g, True, cor_tit)
            tela.blit(titulo_surf, (gx + COL_W//2 - titulo_surf.get_width()//2, gy+10))
            pygame.draw.line(tela, cor_g, (gx+10, gy+38), (gx+COL_W-10, gy+38), 1)

            for j, (chave, valor) in enumerate(linhas):
                ly = gy + 50 + j*34
                sc = fonte_stat.render(chave, True, CYBER_DIM)
                tela.blit(sc, (gx+16, ly))
                sv = fonte_ranking.render(valor, True, BRANCO)
                tela.blit(sv, (gx + COL_W - sv.get_width() - 16, ly))
                if j < len(linhas)-1:
                    _linha_alpha(tela, CINZA_ESC, 80, (gx+16, ly+28), (gx+COL_W-16, ly+28))

        # ── Rodapé padrão ────────────────────────────────────────
        _glow_text(tela, fonte_mini, "ESC  VOLTAR", CYBER_DIM,
                   (LARGURA//2, ALTURA - 18), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:   pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    SOM_VOLTAR.play(); return


# ================================================================
# TELA DE SKINS — APRIMORADA
# ================================================================
def tela_skins(dados: dict) -> None:
    t            = 0.0
    skin_keys    = list(SKINS_CUSTO.keys())
    idx          = skin_keys.index(dados.get("skin_ativa", "classico"))
    mensagem     = ""
    msg_timer    = 0
    anim_in      = 0.0

    TITULO_Y = 46
    GRADE_Y  = TITULO_Y + 106

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.02; anim_in = min(1.0, anim_in + 0.07)
        slide = int((1.0 - anim_in) * -60 * (1.0 - anim_in))

        # ── Título padrão ────────────────────────────────────────
        _glow_text(tela, fonte_titulo, "SKINS", VERDE_NEO,
                   (LARGURA//2, TITULO_Y + slide), centro=True, glow_r=5)
        sub = fonte_peq.render(f"{dados['moedas']} moedas disponíveis", True, DOURADO)
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, TITULO_Y + 72 + slide))

        # ── Grade de skins 4×3 ───────────────────────────────────
        card_w, card_h = 300, 152
        cols, rows     = 4, 3
        total_w        = cols*card_w + (cols-1)*12
        start_x        = LARGURA//2 - total_w//2
        start_y        = GRADE_Y + slide

        for i, skin in enumerate(skin_keys):
            col  = i % cols;  row = i // cols
            cx   = start_x + col*(card_w+12)
            cy   = start_y + row*(card_h+10)

            ativo        = (skin == dados["skin_ativa"])
            selecionado  = (i == idx)
            desbloqueado = skin in dados["skins_desbloqueadas"]

            if selecionado:
                pulse = abs(math.sin(t*4))
                cor_b = tuple(min(255, int(VERDE_NEO[k]*0.5 + CIANO[k]*0.5 + pulse*40)) for k in range(3))
                borda = 3
            elif ativo:
                cor_b = VERDE_NEO; borda = 2
            elif desbloqueado:
                cor_b = CYBER_BORDA; borda = 1
            else:
                cor_b = CINZA_ESC; borda = 1

            _painel_cyber(tela, (cx, cy, card_w, card_h),
                          cor_borda=cor_b, alpha=220, borda=borda, raio=10)

            paleta = PALETA_SKINS.get(skin)
            for seg in range(6):
                if paleta is None:
                    h_val = (seg*36 + t*70) % 360
                    seg_cor = _hsv(h_val, 1.0, 1.0)
                else:
                    ft = seg/5
                    seg_cor = tuple(int(paleta[0][k]*(1-ft)+paleta[1][k]*ft) for k in range(3))
                sx = cx + 10 + seg*46
                sy = cy + 36
                if not desbloqueado:
                    seg_cor = tuple(c//3 for c in seg_cor)
                if skin == "tigre" and seg % 2 == 1:
                    seg_cor = tuple(c//5 for c in seg_cor)
                if selecionado:
                    pulse_s = abs(math.sin(t*5 + seg*0.5))
                    seg_cor = tuple(min(255, int(c*(0.8 + pulse_s*0.4))) for c in seg_cor)
                pygame.draw.rect(tela, seg_cor, (sx, sy, 36, 28), border_radius=6)
                if seg == 0:
                    pygame.draw.circle(tela, BRANCO, (sx+28, sy+8), 5)
                    pygame.draw.circle(tela, PRETO,  (sx+28, sy+8), 3)

            if not desbloqueado:
                lk = fonte_peq.render("BLOQUEADA", True, CINZA)
                tela.blit(lk, (cx+card_w//2-lk.get_width()//2, cy+14))

            cor_nome = BRANCO if desbloqueado else CINZA
            nome = fonte_peq.render(NOMES_SKINS.get(skin, skin), True, cor_nome)
            tela.blit(nome, (cx+card_w//2-nome.get_width()//2, cy+card_h-46))

            custo = SKINS_CUSTO[skin]
            if desbloqueado:
                label = "EQUIPADA" if ativo else "DESBLOQUEADA"
                cor_l = VERDE_NEO if ativo else TEAL
                s_txt = fonte_mini.render(label, True, cor_l)
                tela.blit(s_txt, (cx+card_w//2-s_txt.get_width()//2, cy+card_h-24))
            else:
                cor_c = DOURADO if dados["moedas"] >= custo else VERMELHO
                s_txt = fonte_mini.render(f"{custo} moedas", True, cor_c)
                tela.blit(s_txt, (cx+card_w//2-s_txt.get_width()//2, cy+card_h-24))
                prog = min(1.0, dados["moedas"] / custo if custo > 0 else 1.0)
                _barra_progresso(tela, (cx+12, cy+card_h-10, card_w-24, 6),
                                 prog, cor_c, CINZA_ESC, raio=3)

        # ── Rodapé padrão ────────────────────────────────────────
        skin_at = skin_keys[idx]; desbloq = skin_at in dados["skins_desbloqueadas"]
        if desbloq:
            instrucao = "ENTER  equipar      ESC  voltar      < >  navegar"
        else:
            custo_at = SKINS_CUSTO[skin_at]
            if dados["moedas"] >= custo_at:
                instrucao = f"ENTER  comprar ({custo_at} moedas)    ESC  voltar    < >  navegar"
            else:
                instrucao = f"Faltam {custo_at-dados['moedas']} moedas    ESC  voltar    < >  navegar"
        _glow_text(tela, fonte_peq, instrucao, CYBER_DIM,
                   (LARGURA//2, ALTURA - 38), centro=True)

        if msg_timer > 0:
            msg_timer -= 1
            alpha_m = min(255, msg_timer * 6)
            s_m = fonte_med.render(mensagem, True, VERDE_NEO)
            s_m.set_alpha(alpha_m)
            tela.blit(s_m, (LARGURA//2-s_m.get_width()//2, ALTURA-76))

        _glow_text(tela, fonte_mini, "ESC  VOLTAR", CYBER_DIM,
                   (LARGURA//2, ALTURA - 18), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    SOM_VOLTAR.play(); return
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    SOM_BOTAO.play(); idx = (idx-1) % len(skin_keys)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    SOM_BOTAO.play(); idx = (idx+1) % len(skin_keys)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    skin_sel = skin_keys[idx]
                    if skin_sel in dados["skins_desbloqueadas"]:
                        dados["skin_ativa"] = skin_sel
                        salvar_save(dados)
                        SOM_MOEDA.play()
                        mensagem = "Skin equipada!"; msg_timer = 90
                    else:
                        custo = SKINS_CUSTO[skin_sel]
                        if comprar_skin(dados, skin_sel):
                            SOM_DESBLOQUEIO.play()
                            mensagem = f"Desbloqueada!  (-{custo} moedas)"; msg_timer = 120
                        else:
                            SOM_VOLTAR.play()
                            mensagem = "Moedas insuficientes!"; msg_timer = 80


# ================================================================
# CONSTANTES DOS NOVOS MODOS
# ================================================================
MODO_CLASSICO    = "classico"
MODO_ENDLESS     = "endless"
MODO_HARDCORE    = "hardcore"
MODO_TIME_ATTACK = "time_attack"
MODO_BOSS_RUSH   = "boss_rush"
MODO_MULTI_VS    = "multi_versus"

TIME_ATTACK_DURACAO = 90   # segundos
HARDCORE_VIDAS      = 1    # sem segunda chance

# Cores por modo
CORES_MODO = {
    MODO_CLASSICO:    VERDE_NEO,
    MODO_ENDLESS:     CIANO,
    MODO_HARDCORE:    VERMELHO,
    MODO_TIME_ATTACK: DOURADO,
    MODO_BOSS_RUSH:   MAGENTA,
    MODO_MULTI_VS:    LARANJA,
}

NOMES_MODO = {
    MODO_CLASSICO:    "CLASSICO",
    MODO_ENDLESS:     "ENDLESS",
    MODO_HARDCORE:    "HARDCORE",
    MODO_TIME_ATTACK: "TIME ATTACK",
    MODO_BOSS_RUSH:   "BOSS RUSH",
    MODO_MULTI_VS:    "MULTIPLAYER VERSUS",
}

DESC_MODO = {
    MODO_CLASSICO:    "Modo classico com niveis e inimigos IA",
    MODO_ENDLESS:     "Sem fim! Velocidade cresce infinitamente",
    MODO_HARDCORE:    "Uma vida, sem piedade. Voce morre, acabou.",
    MODO_TIME_ATTACK: f"90 segundos para fazer o maximo de pontos!",
    MODO_BOSS_RUSH:   "Enfrente chefes gigantes em sequencia",
    MODO_MULTI_VS:    "P1: WASD  vs  P2: Setas | Elimine o rival!",
}

# Placar separado por modo
SAVE_MODOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake_modos.json")

def carregar_modos_save() -> dict:
    if os.path.exists(SAVE_MODOS_FILE):
        try:
            with open(SAVE_MODOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {m: [] for m in [MODO_ENDLESS, MODO_HARDCORE, MODO_TIME_ATTACK, MODO_BOSS_RUSH,
                             MODO_MULTI_VS]}

def salvar_modos_save(dados_modos: dict) -> None:
    try:
        with open(SAVE_MODOS_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_modos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[MODOS SAVE] Erro: {e}")

def registrar_placar_modo(dados_modos: dict, modo: str, pontos: int, extra: str = "") -> bool:
    if modo not in dados_modos:
        dados_modos[modo] = []
    entrada = {
        "pontos": pontos,
        "data": datetime.now().strftime("%d/%m %H:%M"),
        "extra": extra,
    }
    dados_modos[modo].append(entrada)
    dados_modos[modo].sort(key=lambda x: x["pontos"], reverse=True)
    dados_modos[modo] = dados_modos[modo][:5]
    salvar_modos_save(dados_modos)
    return any(e is entrada for e in dados_modos[modo])


# ================================================================
# TELA DE SELEÇÃO DE MODO
# ================================================================
def tela_selecao_modo(dados: dict) -> Optional[str]:
    """Retorna string do modo selecionado ou None se ESC."""
    modos = [
        MODO_CLASSICO, MODO_ENDLESS, MODO_HARDCORE,
        MODO_TIME_ATTACK, MODO_BOSS_RUSH,
        MODO_MULTI_VS,
    ]
    idx = 0; t = 0.0; anim_in = 0.0
    dados_modos = carregar_modos_save()

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.02; anim_in = min(1.0, anim_in + 0.07)
        slide = int((1.0 - anim_in)**2 * -80)

        # ── Título padrão ────────────────────────────────────────
        TITULO_Y = 46
        pulse_t = abs(math.sin(t * 2.5))
        cor_tit = tuple(int(MAGENTA[k]*(0.7+pulse_t*0.3)) for k in range(3))
        _glow_text(tela, fonte_titulo, "MODOS DE JOGO", cor_tit,
                   (LARGURA//2, TITULO_Y+slide), centro=True, glow_r=5, glow_cor=ROXO_BRILHO)
        sub = fonte_peq.render("ESCOLHA SEU MODO DE JOGO", True, CYBER_DIM)
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, TITULO_Y + 68 + slide))

        # ── Layout: dois painéis simétricos centralizados ──
        MARGEM    = 36          # margem lateral de cada lado
        GAP       = 16          # espaço entre os dois painéis
        ITEM_H    = 56          # altura de cada item da lista
        ITEM_PAD  = 6           # padding vertical dentro do painel
        LISTA_Y   = TITULO_Y + 100
        lista_h   = len(modos) * ITEM_H + ITEM_PAD * 2
        # Divide o espaço disponível 45% lista / 55% detalhes
        espaco    = LARGURA - MARGEM * 2 - GAP
        lista_w   = int(espaco * 0.42)
        det_w     = espaco - lista_w
        lista_x   = MARGEM
        det_x     = lista_x + lista_w + GAP
        lista_y   = LISTA_Y + slide
        det_y     = lista_y
        det_h     = lista_h

        _painel_cyber(tela, (lista_x, lista_y, lista_w, lista_h), cor_borda=CYBER_BORDA, alpha=220, raio=10)

        for i, modo in enumerate(modos):
            oy = lista_y + ITEM_PAD + i * ITEM_H
            sel = (i == idx)
            cor_m = CORES_MODO[modo]
            if sel:
                pulse_s = abs(math.sin(t*4))
                hl = pygame.Surface((lista_w-16, ITEM_H-4), pygame.SRCALPHA)
                hl.fill((*cor_m, int(22+pulse_s*22)))
                tela.blit(hl, (lista_x+8, oy+2))
                pygame.draw.rect(tela, cor_m, (lista_x+6, oy+4, 4, ITEM_H-8), border_radius=2)
                _glow_text(tela, fonte_hud, NOMES_MODO[modo], cor_m,
                           (lista_x+22, oy + ITEM_H//2 - 14), glow_r=2)
            else:
                s_op = fonte_hud.render(NOMES_MODO[modo], True, CYBER_DIM)
                tela.blit(s_op, (lista_x+22, oy + ITEM_H//2 - 14))
            # Linha separadora
            if i < len(modos)-1:
                _linha_alpha(tela, CINZA_ESC, 60,
                             (lista_x+12, oy+ITEM_H-1), (lista_x+lista_w-12, oy+ITEM_H-1))

        # Painel de detalhes do modo selecionado
        modo_sel = modos[idx]
        cor_sel = CORES_MODO[modo_sel]
        _painel_cyber(tela, (det_x, det_y, det_w, det_h), cor_borda=cor_sel, alpha=230, raio=10)

        pulse_d = abs(math.sin(t*3))
        cor_nome = tuple(min(255, int(cor_sel[k]*(0.8+pulse_d*0.2))) for k in range(3))
        _glow_text(tela, fonte_med, NOMES_MODO[modo_sel], cor_nome,
                   (det_x+det_w//2, det_y+28), centro=True, glow_r=3)
        pygame.draw.line(tela, cor_sel, (det_x+16, det_y+54), (det_x+det_w-16, det_y+54), 1)

        # Descrição
        desc = DESC_MODO[modo_sel]
        palavras = desc.split(); linha_atual = ""; linhas_desc = []
        for p in palavras:
            teste = linha_atual + (" " if linha_atual else "") + p
            if fonte_peq.size(teste)[0] < det_w - 30:
                linha_atual = teste
            else:
                if linha_atual: linhas_desc.append(linha_atual)
                linha_atual = p
        if linha_atual: linhas_desc.append(linha_atual)
        desc_y0 = det_y + 66
        for li, ln in enumerate(linhas_desc):
            s = fonte_peq.render(ln, True, CYBER_TEXTO)
            tela.blit(s, (det_x+16, desc_y0 + li*28))

        # Top 5 do modo (exceto classico)
        if modo_sel != MODO_CLASSICO:
            top = dados_modos.get(modo_sel, [])
            py_top = desc_y0 + len(linhas_desc)*28 + 16
            tela.blit(fonte_mini.render("TOP 5", True, cor_sel), (det_x+16, py_top))
            pygame.draw.line(tela, cor_sel, (det_x+16, py_top+18), (det_x+det_w-16, py_top+18), 1)
            if not top:
                tela.blit(fonte_mini.render("Sem partidas ainda", True, CINZA), (det_x+16, py_top+24))
            else:
                for ri, ent in enumerate(top[:5]):
                    cores_r = [DOURADO, (200,200,210), (200,120,50), CYBER_TEXTO, CYBER_DIM]
                    cor_r = cores_r[min(ri, 4)]
                    linha_r = f"{ri+1}. {ent['pontos']:,}  {ent.get('extra','')}"
                    tela.blit(fonte_mini.render(linha_r, True, cor_r), (det_x+16, py_top+24+ri*22))

        # ── Rodapé padrão ────────────────────────────────────────
        _glow_text(tela, fonte_mini, "ENTER  jogar     ESC  voltar     W/S  navegar",
                   CYBER_DIM, (LARGURA//2, ALTURA - 18), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    SOM_BOTAO.play(); idx = (idx-1) % len(modos)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    SOM_BOTAO.play(); idx = (idx+1) % len(modos)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    SOM_BOTAO.play(); return modos[idx]
                elif ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    SOM_VOLTAR.play(); return None


# ================================================================
# BOSS — CHEFE GIGANTE PARA BOSS RUSH
# ================================================================
class Boss:
    """Cobra gigante com padrões de ataque especiais."""
    FASES = [
        {"nome": "SERPENTE VERMELHA", "cor": (255,30,30),  "tamanho": 18, "vida": 14,  "vel_mult": 1.3},
        {"nome": "HIDRA ROXA",        "cor": (160,20,255), "tamanho": 24, "vida": 20, "vel_mult": 1.6},
        {"nome": "DRAGAO DOURADO",    "cor": (255,180,0),  "tamanho": 30, "vida": 28, "vel_mult": 2.0},
        {"nome": "COBRA NEON",        "cor": (0,255,200),  "tamanho": 38, "vida": 36, "vel_mult": 2.5},
    ]

    def __init__(self, fase: int = 0):
        self.fase_idx = min(fase, len(self.FASES)-1)
        cfg = self.FASES[self.fase_idx]
        self.nome     = cfg["nome"]
        self.cor      = cfg["cor"]
        self.tam      = cfg["tamanho"]
        self.vida_max = cfg["vida"]
        self.vida     = cfg["vida"]
        self.vel_mult = cfg["vel_mult"]
        self.direcao  = (1, 0)
        self.pulso    = 0.0
        self.corpo    = self._spawn_corpo()
        self._tick    = 0
        self._pausa_atq = 0  # cooldown para padrão especial

    def _spawn_corpo(self) -> list:
        cx = COLUNAS//2; cy = LINHAS//2
        return [(cx - i, cy) for i in range(self.tam)]

    def _candidatos_validos(self, bloqueados: set) -> list:
        x, y = self.corpo[0]; dx, dy = self.direcao
        todas = [(1,0),(-1,0),(0,1),(0,-1)]
        def ok(nx, ny):
            return (0 <= nx < COLUNAS and 0 <= ny < LINHAS
                    and (nx,ny) not in self.corpo[4:] and (nx,ny) not in bloqueados)
        sem_uturn = [(a,b) for a,b in todas if not (a==-dx and b==-dy)]
        validas   = [(a,b) for a,b in sem_uturn if ok(x+a, y+b)]
        return validas or [(a,b) for a,b in todas if ok(x+a, y+b)]

    def mover(self, player_pos: tuple, bloqueados: set,
              player_corpo: list = None) -> None:
        self._tick += 1
        self._pausa_atq -= 1
        x, y = self.corpo[0]
        px, py = player_pos

        candidatos = self._candidatos_validos(bloqueados)
        if not candidatos:
            self.corpo.insert(0, (x + self.direcao[0], y + self.direcao[1]))
            self.corpo.pop()
            return

        # Escolhe alvo: tenta interceptar a cabeça do jogador (perseguição real)
        # Fase 2+: comportamento errático periódico para dificultar a fuga
        if self.fase_idx >= 1 and self._pausa_atq <= 0 and random.random() < 0.06:
            self.direcao = random.choice(candidatos)
            self._pausa_atq = 3
        else:
            # Perseguir sempre a cabeça da cobra do jogador
            # Fase 3+: tenta prever 2 passos à frente do jogador
            alvo_x, alvo_y = px, py
            if self.fase_idx >= 2 and player_corpo and len(player_corpo) >= 2:
                # Infere direção do jogador pelos últimos 2 segmentos
                dx_p = player_corpo[0][0] - player_corpo[1][0]
                dy_p = player_corpo[0][1] - player_corpo[1][1]
                passos = 2 + self.fase_idx  # antecipação aumenta por fase
                alvo_x = max(1, min(COLUNAS-2, px + dx_p * passos))
                alvo_y = max(1, min(LINHAS-2,  py + dy_p * passos))

            melhor = None; melhor_score = -999999
            for a, b in candidatos:
                nx, ny = x+a, y+b
                dist = abs(alvo_x-nx)+abs(alvo_y-ny)
                # Fase 3+: aleatoriedade quase zero, perseguição pura
                ruido = 0.1 if self.fase_idx >= 2 else 0.4
                score = -dist + random.uniform(-ruido, ruido)
                if score > melhor_score:
                    melhor_score, melhor = score, (a,b)
            if melhor: self.direcao = melhor

        nova = (x+self.direcao[0], y+self.direcao[1])
        self.corpo.insert(0, nova)
        self.corpo.pop()

    def receber_dano(self) -> bool:
        """Retorna True se o boss morreu."""
        self.vida -= 1
        return self.vida <= 0

    def colide_com(self, pos: tuple) -> bool:
        return pos in self.corpo

    def desenhar(self) -> None:
        self.pulso = (self.pulso + 0.12) % (2*math.pi)
        pv = int(math.sin(self.pulso)*30)
        r, g, b = self.cor
        # Brilho pulsante
        pulse_intensity = abs(math.sin(self.pulso))

        for i, p in enumerate(self.corpo):
            if not (0 <= p[0] < COLUNAS and 0 <= p[1] < LINHAS): continue
            fade = max(0.3, 1.0 - i*0.03)
            cor_seg = (
                max(0,min(255,int(r*fade)+pv)),
                max(0,min(255,int(g*fade)+pv)),
                max(0,min(255,int(b*fade)+pv)),
            )
            # Segmentos maiores no corpo do boss
            tam_seg = GRID - 1 if i > 0 else GRID
            pygame.draw.rect(tela, cor_seg,
                (p[0]*GRID, p[1]*GRID+AREA_JOGO_Y, tam_seg, tam_seg), border_radius=3)
            # Cabeça especial
            if i == 0:
                # Olhos assustadores
                ex, ey = p[0]*GRID, p[1]*GRID+AREA_JOGO_Y
                dx, dy = self.direcao
                o1, o2 = int(GRID*0.7), int(GRID*0.2)
                if   dx==1:  olhos=[(ex+o1,ey+o2),(ex+o1,ey+GRID-o2)]
                elif dx==-1: olhos=[(ex+o2,ey+o2),(ex+o2,ey+GRID-o2)]
                elif dy==-1: olhos=[(ex+o2,ey+o2),(ex+GRID-o2,ey+o2)]
                else:        olhos=[(ex+o2,ey+o1),(ex+GRID-o2,ey+o1)]
                for olho in olhos:
                    pygame.draw.circle(tela, VERMELHO, olho, 5)
                    pygame.draw.circle(tela, (0,0,0), olho, 2)
                # Aura pulsante ao redor da cabeça
                aura_r = int(GRID*0.9 + pulse_intensity*5)
                aura = pygame.Surface((aura_r*2+4, aura_r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(aura, (*self.cor, int(60+40*pulse_intensity)),
                                   (aura_r+2, aura_r+2), aura_r, 2)
                cx = p[0]*GRID+GRID//2; cy = p[1]*GRID+AREA_JOGO_Y+GRID//2
                tela.blit(aura, (cx-aura_r-2, cy-aura_r-2))

    def desenhar_hud_boss(self, fase: int, total_fases: int) -> None:
        """Barra de vida do boss na HUD — estilo cyberpunk aprimorado."""
        t_now  = time.time()
        pulse  = abs(math.sin(t_now * 4))
        frac   = self.vida / self.vida_max
        # Cor da barra: verde (vida cheia) → vermelho (quase morto)
        cor_barra = (
            min(255, int(VERMELHO[0]*(1-frac) + VERDE[0]*frac)),
            min(255, int(VERMELHO[1]*(1-frac) + VERDE[1]*frac)),
            min(255, int(VERMELHO[2]*(1-frac) + VERDE[2]*frac)),
        )
        cor_boss_pulse = tuple(min(255, int(self.cor[k]*(0.5 + pulse*0.5))) for k in range(3))

        # ── Painel central da vida do boss ──────────────────────────
        bw = 640; bh = AREA_JOGO_Y - 8
        bx = LARGURA//2 - bw//2; by = 4
        _painel_cyber(tela, (bx, by, bw, bh), cor_borda=cor_boss_pulse, alpha=220, borda=2, raio=6)

        # Nome do boss — topo centralizado
        nome_s = fonte_mini.render(f"⚔  {self.nome}", True, cor_boss_pulse)
        tela.blit(nome_s, (bx + bw//2 - nome_s.get_width()//2, by + 5))

        # Barra de vida
        bar_x = bx + 10; bar_y = by + 24; bar_w = bw - 20; bar_h = 14
        pygame.draw.rect(tela, (20, 0, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fw = max(0, int(bar_w * frac))
        if fw > 0:
            pygame.draw.rect(tela, cor_barra, (bar_x, bar_y, fw, bar_h), border_radius=4)
            # Brilho interno
            shine = pygame.Surface((fw, bar_h//2), pygame.SRCALPHA)
            shine.fill((*cor_barra, 55))
            tela.blit(shine, (bar_x, bar_y))
        # Marcas de segmento
        for seg in range(1, self.vida_max):
            sx = bar_x + int(bar_w * seg / self.vida_max)
            pygame.draw.line(tela, (0,0,0), (sx, bar_y), (sx, bar_y+bar_h), 1)
        # Borda pulsante da barra
        pygame.draw.rect(tela, cor_boss_pulse, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        # Texto de vida sobre a barra
        vida_s = fonte_mini.render(f"{self.vida} / {self.vida_max}", True, BRANCO)
        tela.blit(vida_s, (bar_x + bar_w//2 - vida_s.get_width()//2, bar_y + 1))

        # ── Badge FASE — direita ─────────────────────────────────────
        fase_w = 110; fase_h = bh
        fx = bx + bw + 8
        _painel_cyber(tela, (fx, by, fase_w, fase_h), cor_borda=DOURADO, alpha=210, borda=2, raio=6)
        f_lbl = fonte_mini.render("FASE", True, DOURADO)
        f_val = fonte_hud.render(f"{fase+1}/{total_fases}", True, DOURADO)
        tela.blit(f_lbl, (fx + fase_w//2 - f_lbl.get_width()//2, by + 5))
        tela.blit(f_val, (fx + fase_w//2 - f_val.get_width()//2, by + 20))


# ================================================================
# MODO BOSS RUSH
# ================================================================
def jogo_boss_rush(dados: dict, dados_modos: dict) -> tuple:
    """Boss Rush: enfrenta chefes em sequencia. Retorna (pontos, fase_chegou)."""
    skin  = dados.get("skin_ativa","classico")
    snake = Snake(skin=skin)
    foods = Foods()
    pontos = 0; fase_atual = 0
    total_fases = len(Boss.FASES)

    boss = Boss(fase=fase_atual)
    inicio = time.time()
    acumulador = 0.0; ultimo_frame = time.time()
    fps_logica = 10.0

    flash_alpha_local = 0; flash_cor_local = BRANCO

    def flash_local(cor, intensidade=120):
        nonlocal flash_alpha_local, flash_cor_local
        flash_alpha_local = intensidade; flash_cor_local = cor

    def desenhar_flash_local():
        nonlocal flash_alpha_local
        if flash_alpha_local > 0:
            s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            s.fill((*flash_cor_local, int(flash_alpha_local))); tela.blit(s, (0,0))
            flash_alpha_local = max(0.0, flash_alpha_local - 8.0)

    sp = {"macas":0,"douradas":0,"inimigos":0,"powerups":0,"combo_max":0}
    combo = 0; combo_timer = 0; multiplicador = 1

    MUSICA.tocar(MODO_BOSS_RUSH)  # Música de fundo do Boss Rush (loop até morrer)

    while True:
        agora = time.time(); delta = min(agora-ultimo_frame, 0.1); ultimo_frame = agora
        acumulador += delta

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if   ev.key in(pygame.K_UP,  pygame.K_w) and snake.direcao!=(0,1):  snake.prox_direcao=(0,-1)
                elif ev.key in(pygame.K_DOWN,pygame.K_s) and snake.direcao!=(0,-1): snake.prox_direcao=(0,1)
                elif ev.key in(pygame.K_LEFT,pygame.K_a) and snake.direcao!=(1,0):  snake.prox_direcao=(-1,0)
                elif ev.key in(pygame.K_RIGHT,pygame.K_d) and snake.direcao!=(-1,0):snake.prox_direcao=(1,0)
                elif ev.key == pygame.K_ESCAPE: MUSICA.parar(); return pontos, fase_atual

        resultado_loop = None
        while acumulador >= 1.0/fps_logica and not resultado_loop:
            acumulador -= 1.0/fps_logica
            snake.mover()

            combo_timer -= 1
            if combo_timer <= 0: combo = multiplicador = 1

            cab = snake.corpo[0]

            # Comida normal
            if cab in foods.normais:
                snake.crescer(); foods.normais.remove(cab)
                excluir = set(snake.corpo)|set(foods.normais)
                foods.normais.append(foods.nova_comida(excluir))
                combo += 1; combo_timer = int(fps_logica*3); multiplicador = 1+combo//3
                pontos += 10*multiplicador; sp["macas"] += 1
                SOM_COMER.play(); adicionar_particulas(cab[0], cab[1], VERDE, 6)

            # Colisão player com corpo do boss
            if boss.colide_com(cab):
                if snake.power:
                    # Acertar o boss com power
                    morreu = boss.receber_dano()
                    pontos += 50*multiplicador
                    flash_local(boss.cor, 100)
                    SOM_PODER if hasattr(SOM_PODER, 'play') else SOM_POWER.play()
                    adicionar_particulas(cab[0], cab[1], boss.cor, 12)
                    if morreu:
                        SOM_NIVEL.play()
                        pontos += 200 + fase_atual*100
                        fase_atual += 1
                        flash_local(DOURADO, 200)
                        # Animação de vitória de fase
                        t0 = time.time()
                        while time.time()-t0 < 1.5:
                            tela.fill(PRETO); _desenhar_grid_cyber()
                            msg = fonte_grande.render(f"BOSS DERROTADO! +{200+fase_atual*100}pts", True, DOURADO)
                            tela.blit(msg, (LARGURA//2-msg.get_width()//2, ALTURA//2-30))
                            pygame.display.update(); clock.tick(60)
                            for e in pygame.event.get():
                                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                        if fase_atual >= total_fases:
                            MUSICA.parar()
                            return pontos, fase_atual  # Venceu todos os bosses!
                        # Próximo boss
                        boss = Boss(fase=fase_atual)
                        fps_logica = 10.0 * boss.vel_mult
                else:
                    flash_local(VERMELHO, 200)
                    resultado_loop = ("gameover", pontos, fase_atual)

            # Boss move
            bloqueados_boss = set(snake.corpo)
            boss.mover(cab, bloqueados_boss, player_corpo=snake.corpo)

            # Colisão própria snake
            if snake.colisao():
                flash_local(VERMELHO, 180)
                resultado_loop = ("gameover", pontos, fase_atual)

        # Render
        tela.fill(PRETO); _desenhar_grid_cyber()
        foods.desenhar()
        boss.desenhar()
        snake.desenhar()
        atualizar_particulas(delta); desenhar_particulas()
        desenhar_flash_local()

        # HUD Boss Rush — magenta/roxo
        _hud_base((8, 0, 12), MAGENTA)
        GAP = 8; x = GAP; CW = AREA_JOGO_Y - 8
        _hud_card(x, "PONTOS", f"{pontos:,}".replace(",","."), MAGENTA, BRANCO, MAGENTA, 190); x += 190+GAP
        _hud_card(x, "COBRA",  str(len(snake.corpo)),           CIANO,   BRANCO, CIANO,   120); x += 120+GAP
        if combo > 1:
            _hud_card(x, "COMBO", f"x{multiplicador}", ROSA, ROSA, ROSA, 130)
        boss.desenhar_hud_boss(fase_atual, total_fases)

        pygame.display.update(); clock.tick(FPS_RENDER)

        if resultado_loop:
            SOM_MORTE.play()
            MUSICA.game_over()  # Para a música do modo e toca o game over
            duracao = time.time()-inicio
            return pontos, fase_atual


# ================================================================
# SNAKE PLAYER 2
# ================================================================
class Snake2(Snake):
    """Snake do jogador 2 com controles de setas."""
    def __init__(self, skin: str = "cyber"):
        super().__init__(skin=skin)

    def reset(self) -> None:
        self.corpo         = [(COLUNAS-11, LINHAS-11), (COLUNAS-10, LINHAS-11), (COLUNAS-9, LINHAS-11)]
        self.direcao       = (-1, 0)
        self.prox_direcao  = (-1, 0)
        self.power         = False
        self.power_time    = 0.0
        self.shield        = False
        self.shield_time   = 0.0
        self.velocidade_boost = False
        self.boost_time    = 0.0
        self.pulso         = math.pi
        self.trail         = []

    def _cor_segmento(self, i: int, pv: int) -> tuple:
        """Player 2 usa paleta azul-ciano."""
        if self.power:
            return (max(0,pv), min(255,180+pv), 255)
        paleta_p2 = [(0, 180, 255), (50, 80, 200)]
        c1, c2 = paleta_p2
        t = max(0.0, min(1.0, i / max(1, len(self.corpo))))
        return tuple(int(c1[k]*(1-t)+c2[k]*t) for k in range(3))


# ================================================================
# HUD MULTIPLAYER
# ================================================================
def desenhar_hud_multi(p1_pts: int, p2_pts: int, snake1: Snake, snake2: Snake2,
                       modo: str, timer_restante: float = 0,
                       p1_vidas: int = 0, p2_vidas: int = 0) -> None:
    """HUD do modo MULTIPLAYER VERSUS — dividida em 3 zonas."""
    _hud_base((6, 6, 14), LARANJA)
    GAP = 8; CARD_H = AREA_JOGO_Y - 8
    HM  = LARGURA // 2   # centro horizontal

    # ── Zona P1 (esquerda) ──────────────────────────────────────
    p1_w = 400
    _painel_cyber(tela, (GAP, 4, p1_w, CARD_H), cor_borda=VERDE_NEO, alpha=210, borda=2, raio=6)
    lbl1 = fonte_mini.render("P1  ·  WASD", True, VERDE_NEO)
    tela.blit(lbl1, (GAP+10, 7))
    pts1 = fonte_hud.render(f"{p1_pts:,}".replace(",","."), True, VERDE_NEO)
    tela.blit(pts1, (GAP + p1_w//2 - pts1.get_width()//2, 22))
    # Vidas P1
    vx = GAP + p1_w - 12
    for v in range(p1_vidas):
        vx -= 18
        pygame.draw.circle(tela, VERDE_NEO, (vx, CARD_H//2 + 4), 6)
        pygame.draw.circle(tela, (0,0,0), (vx, CARD_H//2 + 4), 6, 1)
    # Tamanho cobra P1
    tam1 = fonte_mini.render(f"cobra: {len(snake1.corpo)}", True, BRANCO)
    tela.blit(tam1, (GAP+10, CARD_H - 14))

    # ── Zona central VS ─────────────────────────────────────────
    vs_w = 160
    vs_x = HM - vs_w // 2
    _painel_cyber(tela, (vs_x, 4, vs_w, CARD_H), cor_borda=LARANJA, alpha=220, borda=2, raio=6)
    vs_s = fonte_hud.render("VS", True, LARANJA)
    tela.blit(vs_s, (HM - vs_s.get_width()//2, CARD_H//2 - vs_s.get_height()//2 + 4))

    # ── Zona P2 (direita) ───────────────────────────────────────
    p2_w = 400
    p2_x = LARGURA - GAP - p2_w
    _painel_cyber(tela, (p2_x, 4, p2_w, CARD_H), cor_borda=AZUL, alpha=210, borda=2, raio=6)
    lbl2 = fonte_mini.render("P2  ·  SETAS", True, AZUL)
    tela.blit(lbl2, (p2_x + p2_w - lbl2.get_width() - 10, 7))
    pts2 = fonte_hud.render(f"{p2_pts:,}".replace(",","."), True, AZUL)
    tela.blit(pts2, (p2_x + p2_w//2 - pts2.get_width()//2, 22))
    # Vidas P2
    vx2 = p2_x + 12
    for v in range(p2_vidas):
        pygame.draw.circle(tela, AZUL, (vx2, CARD_H//2 + 4), 6)
        pygame.draw.circle(tela, (0,0,0), (vx2, CARD_H//2 + 4), 6, 1)
        vx2 += 18
    # Tamanho cobra P2
    tam2 = fonte_mini.render(f"cobra: {len(snake2.corpo)}", True, BRANCO)
    tela.blit(tam2, (p2_x + p2_w - tam2.get_width() - 10, CARD_H - 14))


# ================================================================
# TELA DE VITÓRIA MULTIPLAYER
# ================================================================
def tela_vitoria_multi(vencedor: str, p1_pts: int, p2_pts: int, modo: str) -> str:
    """Mostra tela de vitória. Retorna 'jogar' ou 'menu'."""
    t = 0.0; anim_in = 0.0
    partes: list = []
    cor_v = VERDE_NEO if vencedor == "P1" else AZUL if vencedor == "P2" else DOURADO

    for _ in range(60):
        partes.append({
            "x": random.uniform(LARGURA*0.3, LARGURA*0.7),
            "y": random.uniform(ALTURA*0.3, ALTURA*0.6),
            "vx": random.uniform(-4,4), "vy": random.uniform(-5,1),
            "vida": random.randint(50,100),
            "cor": random.choice([cor_v, DOURADO, BRANCO, ROSA]),
            "tam": random.randint(2,5),
        })

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.025; anim_in = min(1.0, anim_in+0.05)
        slide = int((1.0-anim_in)**2 * -80)

        for p in partes[:]:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]
            p["vy"]+=0.1; p["vida"]-=1
            if p["vida"] <= 0: partes.remove(p); continue
            a = min(255, p["vida"]*3)
            s = pygame.Surface((p["tam"]*2,p["tam"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["cor"],a), (p["tam"],p["tam"]), p["tam"])
            tela.blit(s, (int(p["x"])-p["tam"], int(p["y"])-p["tam"]))

        pulse = abs(math.sin(t*3))
        cor_titulo = tuple(min(255,int(cor_v[k]*(0.7+pulse*0.3))) for k in range(3))

        if vencedor in ("P1","P2"):
            _glow_text(tela, fonte_titulo, f"VENCEDOR: {vencedor}!", cor_titulo,
                       (LARGURA//2, 100+slide), centro=True, glow_r=6)
            controle = "WASD" if vencedor=="P1" else "SETAS"
            _glow_text(tela, fonte_med, f"Jogador {vencedor[-1]} ({controle})", cor_titulo,
                       (LARGURA//2, 176+slide), centro=True, glow_r=3)
        else:
            _glow_text(tela, fonte_titulo, "EMPATE!", DOURADO,
                       (LARGURA//2, 100+slide), centro=True, glow_r=6)

        # Painel de placar
        pw = 600; ph = 200
        px = LARGURA//2-pw//2; py = 220+slide
        _painel_cyber(tela, (px, py, pw, ph), cor_borda=cor_v, alpha=230, raio=12)
        tela.blit(fonte_hud.render("PLACAR FINAL", True, CYBER_DIM), (px+pw//2-80, py+12))
        pygame.draw.line(tela, cor_v, (px+16, py+40), (px+pw-16, py+40), 1)

        # P1
        s1 = fonte_grande.render(f"P1: {p1_pts}", True, VERDE_NEO)
        tela.blit(s1, (px+pw//4 - s1.get_width()//2, py+60))
        s1c = fonte_mini.render("WASD", True, VERDE_NEO)
        tela.blit(s1c, (px+pw//4-s1c.get_width()//2, py+130))

        # VS
        sv = fonte_grande.render("VS", True, LARANJA)
        tela.blit(sv, (px+pw//2-sv.get_width()//2, py+60))

        # P2
        s2 = fonte_grande.render(f"P2: {p2_pts}", True, AZUL)
        tela.blit(s2, (px+3*pw//4-s2.get_width()//2, py+60))
        s2c = fonte_mini.render("SETAS", True, AZUL)
        tela.blit(s2c, (px+3*pw//4-s2c.get_width()//2, py+130))

        _glow_text(tela, fonte_med, "ENTER — jogar novamente     ESC — menu",
                   CYBER_DIM, (LARGURA//2, ALTURA-40), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN: return "jogar"
                if ev.key == pygame.K_ESCAPE: return "menu"


# ================================================================
# MODO MULTIPLAYER LOCAL (VERSUS)
# ================================================================
def jogo_multi(dados: dict, dados_modos: dict, modo: str) -> tuple:
    """Modo multiplayer local. Retorna (pontos_p1, pontos_p2, vencedor_str)."""
    skin1 = dados.get("skin_ativa","classico")
    skin2 = "cyber"  # P2 sempre com skin cyber azul

    snake1 = Snake(skin=skin1)
    snake2 = Snake2(skin=skin2)
    foods  = Foods()

    p1_pts = 0; p2_pts = 0
    p1_vidas = 3; p2_vidas = 3

    acumulador = 0.0; ultimo_frame = time.time()
    fps_logica = 9.0

    flash_alpha_l = 0; flash_cor_l = BRANCO

    def flash_l(cor, i=120):
        nonlocal flash_alpha_l, flash_cor_l
        flash_alpha_l = i; flash_cor_l = cor

    def desenhar_flash_l():
        nonlocal flash_alpha_l
        if flash_alpha_l > 0:
            s = pygame.Surface((LARGURA,ALTURA), pygame.SRCALPHA)
            s.fill((*flash_cor_l, int(flash_alpha_l))); tela.blit(s,(0,0))
            flash_alpha_l = max(0.0, flash_alpha_l-8.0)

    inicio = time.time()
    p1_morto = False; p2_morto = False

    MUSICA.tocar(modo)  # Música de fundo do modo (loop até o fim da partida)

    while True:
        agora = time.time(); delta = min(agora-ultimo_frame, 0.1); ultimo_frame = agora
        acumulador += delta

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                # P1: WASD
                if   ev.key == pygame.K_w and snake1.direcao!=(0,1):  snake1.prox_direcao=(0,-1)
                elif ev.key == pygame.K_s and snake1.direcao!=(0,-1): snake1.prox_direcao=(0,1)
                elif ev.key == pygame.K_a and snake1.direcao!=(1,0):  snake1.prox_direcao=(-1,0)
                elif ev.key == pygame.K_d and snake1.direcao!=(-1,0): snake1.prox_direcao=(1,0)
                # P2: Setas
                elif ev.key == pygame.K_UP    and snake2.direcao!=(0,1):  snake2.prox_direcao=(0,-1)
                elif ev.key == pygame.K_DOWN  and snake2.direcao!=(0,-1): snake2.prox_direcao=(0,1)
                elif ev.key == pygame.K_LEFT  and snake2.direcao!=(1,0):  snake2.prox_direcao=(-1,0)
                elif ev.key == pygame.K_RIGHT and snake2.direcao!=(-1,0): snake2.prox_direcao=(1,0)
                elif ev.key == pygame.K_ESCAPE: MUSICA.parar(); return p1_pts, p2_pts, "none"

        resultado_loop = None
        while acumulador >= 1.0/fps_logica and not resultado_loop:
            acumulador -= 1.0/fps_logica

            if not p1_morto: snake1.mover()
            if not p2_morto: snake2.mover()

            # ---- Coleta de comida P1 ----
            if not p1_morto:
                cab1 = snake1.corpo[0]
                if cab1 in foods.normais:
                    snake1.crescer(); foods.normais.remove(cab1)
                    excluir = set(snake1.corpo)|set(snake2.corpo)|set(foods.normais)
                    foods.normais.append(foods.nova_comida(excluir))
                    p1_pts += 10; SOM_COMER.play()
                    adicionar_particulas(cab1[0], cab1[1], VERDE_NEO, 6)
                if foods.dourada and cab1 == foods.dourada:
                    snake1.power = True; snake1.power_time = agora+5
                    foods.dourada = None; p1_pts += 50
                    SOM_POWER.play()
                    adicionar_particulas(cab1[0], cab1[1], DOURADO, 10)

            # ---- Coleta de comida P2 ----
            if not p2_morto:
                cab2 = snake2.corpo[0]
                if cab2 in foods.normais:
                    snake2.crescer(); foods.normais.remove(cab2)
                    excluir = set(snake1.corpo)|set(snake2.corpo)|set(foods.normais)
                    foods.normais.append(foods.nova_comida(excluir))
                    p2_pts += 10; SOM_COMER.play()
                    adicionar_particulas(cab2[0], cab2[1], AZUL, 6)
                if foods.dourada and cab2 == foods.dourada:
                    snake2.power = True; snake2.power_time = agora+5
                    foods.dourada = None; p2_pts += 50
                    SOM_POWER.play()
                    adicionar_particulas(cab2[0], cab2[1], DOURADO, 10)

            # Power timeout (modo VS)
            if snake1.power and agora > snake1.power_time: snake1.power = False
            if snake2.power and agora > snake2.power_time: snake2.power = False

            # ---- Colisões VERSUS ----
            # P1 bate em P2
            if not p1_morto and not p2_morto:
                cab1 = snake1.corpo[0]
                if cab1 in snake2.corpo:
                    if snake1.power and not snake2.power:
                        # P1 elimina P2
                        p2_vidas -= 1; p2_morto = True
                        p1_pts += 100
                        flash_l(VERDE_NEO, 150)
                        SOM_PODER if hasattr(SOM_PODER,'play') else SOM_COMER.play()
                        adicionar_particulas(cab1[0], cab1[1], AZUL, 14)
                    else:
                        p1_vidas -= 1; p1_morto = True
                        flash_l(VERMELHO, 150)
                        SOM_MORTE.play()
                # P2 bate em P1
                cab2 = snake2.corpo[0]
                if cab2 in snake1.corpo:
                    if snake2.power and not snake1.power:
                        p1_vidas -= 1; p1_morto = True
                        p2_pts += 100
                        flash_l(AZUL, 150)
                        SOM_COMER.play()
                        adicionar_particulas(cab2[0], cab2[1], VERDE_NEO, 14)
                    else:
                        p2_vidas -= 1; p2_morto = True
                        flash_l(VERMELHO, 150)
                        SOM_MORTE.play()
                # Colisão de cabeças simultânea
                if not p1_morto and not p2_morto:
                    if snake1.corpo[0] == snake2.corpo[0]:
                        p1_vidas -= 1; p2_vidas -= 1
                        p1_morto = True; p2_morto = True
                        flash_l(DOURADO, 200)

            # Respawn após morte (se ainda tem vidas)
            if p1_morto and p1_vidas > 0:
                snake1 = Snake(skin=skin1); p1_morto = False
            if p2_morto and p2_vidas > 0:
                snake2 = Snake2(skin=skin2); p2_morto = False

            # Colisão com parede/próprio corpo
            if not p1_morto and snake1.colisao():
                p1_vidas -= 1; p1_morto = True; flash_l(VERMELHO, 120); SOM_MORTE.play()
                if p1_vidas > 0: snake1 = Snake(skin=skin1); p1_morto = False
            if not p2_morto and snake2.colisao():
                p2_vidas -= 1; p2_morto = True; flash_l(VERMELHO, 120); SOM_MORTE.play()
                if p2_vidas > 0: snake2 = Snake2(skin=skin2); p2_morto = False

            # Fim: algum jogador sem vidas
            if p1_vidas <= 0 and p2_vidas <= 0:
                resultado_loop = "empate"
            elif p1_vidas <= 0:
                resultado_loop = "P2"
            elif p2_vidas <= 0:
                resultado_loop = "P1"

        # ---- Render ----
        tela.fill(PRETO); _desenhar_grid_cyber()
        foods.desenhar()
        if not p1_morto: snake1.desenhar()
        if not p2_morto: snake2.desenhar()
        atualizar_particulas(delta); desenhar_particulas()
        desenhar_flash_l()
        desenhar_hud_multi(p1_pts, p2_pts, snake1, snake2, modo,
                           p1_vidas=p1_vidas, p2_vidas=p2_vidas)

        # Indicadores de vidas in-game
        for v in range(p1_vidas):
            pygame.draw.circle(tela, VERDE_NEO, (16+v*18, AREA_JOGO_Y+12), 7)
        for v in range(p2_vidas):
            pygame.draw.circle(tela, AZUL, (LARGURA-16-v*18, AREA_JOGO_Y+12), 7)

        pygame.display.update(); clock.tick(FPS_RENDER)

        if resultado_loop:
            MUSICA.game_over()  # Para a música do modo e toca o game over
            t0 = time.time()
            while time.time()-t0 < 0.5:
                tela.fill(PRETO); _desenhar_grid_cyber()
                foods.desenhar()
                if not p1_morto: snake1.desenhar()
                if not p2_morto: snake2.desenhar()
                desenhar_flash_l()
                pygame.display.update(); clock.tick(FPS_RENDER)
            if resultado_loop == "gameover":
                return p1_pts, p2_pts, ("P1" if p1_pts >= p2_pts else "P2")
            elif resultado_loop == "empate":
                return p1_pts, p2_pts, "empate"
            else:
                return p1_pts, p2_pts, resultado_loop


# ================================================================
# MODO ENDLESS
# ================================================================
def jogo_endless(dados: dict, dados_modos: dict) -> int:
    """Endless: sem inimigos IA, velocidade cresce continuamente."""
    skin  = dados.get("skin_ativa","classico")
    snake = Snake(skin=skin)
    foods = Foods()
    foods.dourada = None   # sem maçã dourada no endless
    pontos = 0; macas = 0
    combo = 0; combo_timer = 0; multiplicador = 1

    # Power-up de multiplicador
    multi_pw_valor   = 1
    multi_pw_expira  = 0.0
    multi_pw_expirou = False

    inicio = time.time(); acumulador = 0.0; ultimo_frame = time.time()
    velocidade_base = 8.0; velocidade_atual = velocidade_base

    MUSICA.tocar(MODO_ENDLESS)  # Música de fundo do Endless (loop até morrer)

    while True:
        agora = time.time(); delta = min(agora-ultimo_frame, 0.1); ultimo_frame = agora
        # Velocidade cresce com o tempo e pontos
        velocidade_atual = velocidade_base + macas*0.15 + (agora-inicio)*0.008
        velocidade_atual = min(velocidade_atual, 30.0)
        acumulador += delta

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if   ev.key in(pygame.K_UP,  pygame.K_w) and snake.direcao!=(0,1):  snake.prox_direcao=(0,-1)
                elif ev.key in(pygame.K_DOWN,pygame.K_s) and snake.direcao!=(0,-1): snake.prox_direcao=(0,1)
                elif ev.key in(pygame.K_LEFT,pygame.K_a) and snake.direcao!=(1,0):  snake.prox_direcao=(-1,0)
                elif ev.key in(pygame.K_RIGHT,pygame.K_d) and snake.direcao!=(-1,0):snake.prox_direcao=(1,0)
                elif ev.key == pygame.K_ESCAPE: MUSICA.parar(); return pontos

        resultado_loop = None
        while acumulador >= 1.0/velocidade_atual and not resultado_loop:
            acumulador -= 1.0/velocidade_atual
            snake.mover()

            if snake.power and agora > snake.power_time: snake.power = False
            combo_timer -= 1
            if combo_timer <= 0: combo = multiplicador = 1

            # Expiração do multiplicador
            if multi_pw_valor > 1 and agora >= multi_pw_expira:
                multi_pw_valor = 1; multi_pw_expirou = True

            cab = snake.corpo[0]
            if cab in foods.normais:
                snake.crescer(); foods.normais.remove(cab)
                excluir = set(snake.corpo)|set(foods.normais)
                foods.normais.append(foods.nova_comida(excluir))
                foods.tentar_spawn_multi(excluir | set(foods.normais))
                combo += 1; combo_timer = int(velocidade_atual*3); multiplicador = 1+combo//3
                pontos += 10*multiplicador*multi_pw_valor; macas += 1
                SOM_COMER.play(); adicionar_particulas(cab[0], cab[1], VERDE_NEO, 6)
            if foods.multi_pw and cab == foods.multi_pw[0]:
                pos, valor = foods.multi_pw; foods.multi_pw = None
                multi_pw_valor = valor; multi_pw_expira = agora + MULTI_DURACAO
                multi_pw_expirou = False
                SOM_MULTI_PEGAR.play()
                adicionar_particulas(pos[0], pos[1], MULTI_CORES.get(valor, CIANO), 16)
                flash(MULTI_CORES.get(valor, CIANO), 100)

            if snake.colisao():
                flash(VERMELHO, 180); resultado_loop = "gameover"

        # Render
        tela.fill(PRETO); _desenhar_grid_cyber()
        foods.desenhar(); snake.desenhar()
        atualizar_particulas(delta); desenhar_particulas(); desenhar_flash()
        if multi_pw_expirou: SOM_MULTI_FIM.play(); multi_pw_expirou = False

        # HUD Endless — tema ciano
        restante_pw = max(0.0, multi_pw_expira - agora) if multi_pw_valor > 1 else 0.0
        _hud_base((4, 10, 16), CIANO)
        GAP = 8; x = GAP
        _hud_card(x, "ENDLESS",    "∞",                              CIANO,   CIANO,  CIANO,   90);  x += 90+GAP
        _hud_card(x, "PONTOS",     f"{pontos:,}".replace(",","."),   CIANO,   BRANCO, CIANO,   190); x += 190+GAP
        _hud_card(x, "COBRA",      str(len(snake.corpo)),             VERDE_NEO,BRANCO,VERDE_NEO,120); x += 120+GAP
        # Barra de velocidade
        _hud_card(x, "VELOCIDADE", f"{velocidade_atual:.1f}",         CIANO,   BRANCO, CIANO,   150); x += 150+GAP
        # Lado direito
        rx = LARGURA - GAP
        if multi_pw_valor > 1 and restante_pw > 0:
            cor_pw = MULTI_CORES.get(multi_pw_valor, CIANO)
            pw_w = 170; rx -= pw_w + GAP
            _painel_cyber(tela, (rx, 4, pw_w, AREA_JOGO_Y-8), cor_borda=cor_pw, alpha=210, borda=2, raio=5)
            lbl_pw = fonte_mini.render(f"×{multi_pw_valor} POWER", True, cor_pw)
            tela.blit(lbl_pw, (rx + pw_w//2 - lbl_pw.get_width()//2, 7))
            frac = max(0.0, min(1.0, restante_pw / MULTI_DURACAO))
            bw = pw_w - 12
            pygame.draw.rect(tela, CINZA_ESC, (rx+6, 30, bw, 6), border_radius=3)
            pygame.draw.rect(tela, cor_pw,    (rx+6, 30, int(bw*frac), 6), border_radius=3)
            rx -= GAP
        if combo > 1:
            cw = 130; rx -= cw + GAP
            _hud_card(rx, "COMBO", f"x{multiplicador}", ROSA, ROSA, ROSA, cw)
        pygame.display.update(); clock.tick(FPS_RENDER)

        if resultado_loop:
            SOM_MORTE.play(); MUSICA.game_over(); return pontos


# ================================================================
# MODO HARDCORE
# ================================================================
def jogo_hardcore(dados: dict, dados_modos: dict) -> int:
    """Hardcore: uma vida, sem segunda chance, inimigos mais agressivos."""
    skin  = dados.get("skin_ativa","classico")
    snake = Snake(skin=skin)
    foods = Foods()
    pontos = 0; nivel = 1; combo = 0; combo_timer = 0; multiplicador = 1

    inimigos = criar_inimigos(nivel, snake.corpo)
    for bot in inimigos:
        for pers in list(Personalidade):
            bot.personalidade = Personalidade.AGRESSIVA  # todos agressivos

    inicio = time.time(); acumulador = 0.0; ultimo_frame = time.time()
    sp = {"macas":0,"douradas":0,"inimigos":0,"powerups":0,"combo_max":0}

    MUSICA.tocar(MODO_HARDCORE)  # Música de fundo do Hardcore (loop até morrer)

    while True:
        agora = time.time(); delta = min(agora-ultimo_frame, 0.1); ultimo_frame = agora
        fps_logica = (FPS_BASE+(nivel-1)*(FPS_MAX-FPS_BASE)/9) * 1.7  # 70% mais rápido no hardcore
        acumulador += delta

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if   ev.key in(pygame.K_UP,  pygame.K_w) and snake.direcao!=(0,1):  snake.prox_direcao=(0,-1)
                elif ev.key in(pygame.K_DOWN,pygame.K_s) and snake.direcao!=(0,-1): snake.prox_direcao=(0,1)
                elif ev.key in(pygame.K_LEFT,pygame.K_a) and snake.direcao!=(1,0):  snake.prox_direcao=(-1,0)
                elif ev.key in(pygame.K_RIGHT,pygame.K_d) and snake.direcao!=(-1,0):snake.prox_direcao=(1,0)
                elif ev.key == pygame.K_ESCAPE: MUSICA.parar(); return pontos

        resultado_loop = None
        while acumulador >= 1.0/fps_logica and not resultado_loop:
            acumulador -= 1.0/fps_logica
            snake.mover()
            if snake.power and agora > snake.power_time: snake.power = False
            combo_timer -= 1
            if combo_timer <= 0: combo = multiplicador = 1

            novo_nivel = nivel_para_pontos(pontos)
            if novo_nivel > nivel:
                nivel = novo_nivel; inimigos = criar_inimigos(nivel, snake.corpo)
                for bot in inimigos: bot.personalidade = Personalidade.AGRESSIVA
                excluir_lv=set(snake.corpo)|set(foods.normais)
                foods.ajustar_macas_nivel(nivel, excluir_lv)
                MUSICA.acelerar(nivel)  # Acelera a música conforme o nível

            cab = snake.corpo[0]
            if cab in foods.normais:
                snake.crescer(); foods.normais.remove(cab)
                excluir = set(snake.corpo)|set(foods.normais)
                foods.normais.append(foods.nova_comida(excluir))
                combo += 1; combo_timer = int(fps_logica*3); multiplicador = 1+combo//3
                pontos += 10*multiplicador; sp["macas"] += 1
                SOM_COMER.play(); adicionar_particulas(cab[0], cab[1], VERMELHO, 6)
            if foods.dourada and cab == foods.dourada:
                snake.power=True; snake.power_time=agora+5; foods.dourada=None
                pontos+=50*multiplicador; sp["douradas"]+=1
                SOM_POWER.play(); adicionar_particulas(cab[0], cab[1], DOURADO, 10)
                # Respawna nova maca dourada imediatamente
                excluir_d=set(snake.corpo)|set(foods.normais)
                foods.dourada=foods.nova_comida(excluir_d)

            # Garante que a maca dourada sempre existe no hardcore
            if foods.dourada is None:
                excluir_d=set(snake.corpo)|set(foods.normais)
                foods.dourada=foods.nova_comida(excluir_d)

            for bot in inimigos:
                bot.nivel_jogo = nivel
                # Hardcore: bots sempre no pico de agressividade, nunca hesitam
                bot._humor = 1.0
                bot.mover(foods.normais, cab, [b.corpo for b in inimigos if b is not bot]+[snake.corpo],
                          player_direcao=snake.direcao, player_power=snake.power,
                          dourada_pos=foods.dourada, aliados=inimigos)

            bots_rem = []
            for i, bot in enumerate(inimigos):
                cbx,cby = bot.corpo[0]
                if snake.corpo[0] in bot.corpo[1:] or snake.corpo[0] == bot.corpo[0]:
                    if snake.power and not bot.power:
                        bots_rem.append(i); pontos += 30*multiplicador; sp["inimigos"]+=1
                        SOM_COMER.play(); adicionar_particulas(cbx,cby,bot.cor,10)
                    else: flash(VERMELHO,180); resultado_loop = "gameover"
            for i in sorted(set(bots_rem), reverse=True):
                if i < len(inimigos): inimigos.pop(i)

            if snake.colisao(): flash(VERMELHO,180); resultado_loop = "gameover"

        # Render
        tela.fill(PRETO); _desenhar_grid_cyber()
        foods.desenhar()
        for bot in inimigos: bot.desenhar()
        snake.desenhar()
        atualizar_particulas(delta); desenhar_particulas(); desenhar_flash()

        # HUD Hardcore — vermelho/sangue
        _pulse_hc = abs(math.sin(time.time() * 3))
        _cor_hc   = tuple(min(255, int(VERMELHO[k] * (0.6 + _pulse_hc * 0.4))) for k in range(3))
        _hud_base((12, 0, 0), _cor_hc)
        GAP = 8; x = GAP
        # Badge modo
        _painel_cyber(tela, (x, 4, 108, AREA_JOGO_Y-8), cor_borda=_cor_hc, alpha=200, borda=2, raio=5)
        _glow_text(tela, fonte_hud, "HARD", _cor_hc, (x+54, AREA_JOGO_Y//2+2), centro=True, glow_r=2)
        x += 108 + GAP
        _hud_card(x, "PONTOS", f"{pontos:,}".replace(",","."), VERMELHO, BRANCO, VERMELHO, 190); x += 190+GAP
        _hud_card(x, "NÍVEL",  str(nivel),                    DOURADO,  DOURADO, DOURADO,  110); x += 110+GAP
        _hud_card(x, "COBRA",  str(len(snake.corpo)),          CIANO,   BRANCO,  CIANO,   110); x += 110+GAP
        if combo > 1:
            _hud_card(x, "COMBO", f"x{multiplicador}", ROSA, ROSA, ROSA, 120)
        # Aviso direita — pulsante
        aw = 250
        _painel_cyber(tela, (LARGURA-aw-GAP, 4, aw, AREA_JOGO_Y-8), cor_borda=_cor_hc, alpha=200, borda=2, raio=5)
        _aviso_cor = tuple(min(255, int(VERMELHO[k]*(0.4+_pulse_hc*0.6))) for k in range(3))
        _glow_text(tela, fonte_mini, "⚠   1 VIDA", _aviso_cor,
                   (LARGURA - aw//2 - GAP, AREA_JOGO_Y//2 + 2), centro=True, glow_r=2)

        pygame.display.update(); clock.tick(FPS_RENDER)

        if resultado_loop:
            SOM_MORTE.play(); MUSICA.game_over(); return pontos


# ================================================================
# MODO TIME ATTACK
# ================================================================
def jogo_time_attack(dados: dict, dados_modos: dict) -> int:
    """Time Attack: 90 segundos para pontuar o máximo."""
    skin  = dados.get("skin_ativa","classico")
    snake = Snake(skin=skin)
    foods = Foods()
    pontos = 0; combo = 0; combo_timer = 0; multiplicador = 1

    inicio = time.time(); acumulador = 0.0; ultimo_frame = time.time()
    fps_logica = 10.0

    MUSICA.tocar(MODO_TIME_ATTACK)  # Música de fundo do Time Attack (loop até o tempo acabar)

    while True:
        agora = time.time(); delta = min(agora-ultimo_frame, 0.1); ultimo_frame = agora
        tempo_restante = max(0.0, TIME_ATTACK_DURACAO - (agora-inicio))
        acumulador += delta

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if   ev.key in(pygame.K_UP,  pygame.K_w) and snake.direcao!=(0,1):  snake.prox_direcao=(0,-1)
                elif ev.key in(pygame.K_DOWN,pygame.K_s) and snake.direcao!=(0,-1): snake.prox_direcao=(0,1)
                elif ev.key in(pygame.K_LEFT,pygame.K_a) and snake.direcao!=(1,0):  snake.prox_direcao=(-1,0)
                elif ev.key in(pygame.K_RIGHT,pygame.K_d) and snake.direcao!=(-1,0):snake.prox_direcao=(1,0)
                elif ev.key == pygame.K_ESCAPE: MUSICA.parar(); return pontos

        if tempo_restante <= 0:
            MUSICA.game_over()  # Para a música do modo e toca o game over
            return pontos

        resultado_loop = None
        while acumulador >= 1.0/fps_logica and not resultado_loop:
            acumulador -= 1.0/fps_logica
            snake.mover()
            if snake.power and agora > snake.power_time: snake.power = False
            combo_timer -= 1
            if combo_timer <= 0: combo = multiplicador = 1

            cab = snake.corpo[0]
            if cab in foods.normais:
                snake.crescer(); foods.normais.remove(cab)
                excluir = set(snake.corpo)|set(foods.normais)
                foods.normais.append(foods.nova_comida(excluir))
                combo += 1; combo_timer = int(fps_logica*3); multiplicador = 1+combo//3
                pontos += 10*multiplicador
                SOM_COMER.play(); adicionar_particulas(cab[0], cab[1], DOURADO, 6)
            if foods.dourada and cab == foods.dourada:
                snake.power=True; snake.power_time=agora+5; foods.dourada=None
                pontos+=50*multiplicador
                SOM_POWER.play(); adicionar_particulas(cab[0], cab[1], DOURADO, 10)

            if snake.colisao():
                flash(VERMELHO, 180); resultado_loop = "morreu"
                pontos = max(0, pontos-50)  # penalidade por morrer
                combo = 0; multiplicador = 1; combo_timer = 0

        # Render
        tela.fill(PRETO); _desenhar_grid_cyber()
        foods.desenhar(); snake.desenhar()
        atualizar_particulas(delta); desenhar_particulas(); desenhar_flash()

        # HUD Time Attack — dourado/âmbar
        cor_timer = VERMELHO if tempo_restante < 15 else DOURADO
        _hud_base((14, 10, 0), cor_timer)

        # Barra de tempo na base da HUD
        frac_t = tempo_restante / TIME_ATTACK_DURACAO
        barra_w_t = int(LARGURA * frac_t)
        pygame.draw.rect(tela, CINZA_ESC, (0, AREA_JOGO_Y - 5, LARGURA, 5))
        pygame.draw.rect(tela, cor_timer,  (0, AREA_JOGO_Y - 5, barra_w_t, 5))

        GAP = 8; x = GAP
        _hud_card(x, "TIME",   "ATTACK",                            DOURADO, DOURADO, DOURADO, 110); x += 110+GAP
        _hud_card(x, "PONTOS", f"{pontos:,}".replace(",","."),      DOURADO, BRANCO,  DOURADO, 190); x += 190+GAP
        _hud_card(x, "COBRA",  str(len(snake.corpo)),                VERDE_NEO,BRANCO, VERDE_NEO,120); x += 120+GAP
        if combo > 1:
            _hud_card(x, "COMBO", f"x{multiplicador}", ROSA, ROSA, ROSA, 120)

        # Timer central grande
        tw = 140; tx = LARGURA//2 - tw//2
        _painel_cyber(tela, (tx, 2, tw, AREA_JOGO_Y-6), cor_borda=cor_timer, alpha=230, borda=2, raio=6)
        ts = fonte_grande.render(f"{int(tempo_restante)}s", True, cor_timer)
        tela.blit(ts, (LARGURA//2 - ts.get_width()//2, 0))

        pygame.display.update(); clock.tick(FPS_RENDER)

        if resultado_loop == "morreu":
            SOM_MORTE.play()
            # Breve pausa de morte com flash
            t0 = time.time()
            while time.time()-t0 < 0.4:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                tela.fill(PRETO); _desenhar_grid_cyber()
                foods.desenhar(); desenhar_flash()
                pygame.display.update(); clock.tick(FPS_RENDER)
            # Respawna a cobra no centro, jogo continua
            snake = Snake(skin=skin)
            acumulador = 0.0


# ================================================================
# TELA DE RESULTADO MODO ESPECIAL
# ================================================================
def tela_resultado_modo(modo: str, pontos: int, dados_modos: dict,
                        extra_info: str = "", cor_modo: tuple = None) -> str:
    """Tela de resultado para modos especiais. Retorna 'jogar' ou 'menu'."""
    cor_m = cor_modo or CORES_MODO.get(modo, VERDE_NEO)
    top5  = dados_modos.get(modo, [])
    eh_recorde = bool(top5) and pontos >= top5[0]["pontos"] if top5 else True
    posicao = None
    for i, e in enumerate(top5):
        if e["pontos"] == pontos: posicao = i+1; break

    t = 0.0; anim_in = 0.0
    partes: list = []
    for _ in range(50):
        partes.append({
            "x": random.uniform(LARGURA*0.25, LARGURA*0.75),
            "y": random.uniform(ALTURA*0.25, ALTURA*0.65),
            "vx": random.uniform(-3.5,3.5), "vy": random.uniform(-4.5,0.5),
            "vida": random.randint(50,100),
            "cor": random.choice([cor_m, DOURADO, ROSA, BRANCO]),
            "tam": random.randint(2,5),
        })

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.025; anim_in = min(1.0, anim_in+0.055)
        slide = int((1.0-anim_in)**2 * -80)

        for p in partes[:]:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=0.1; p["vida"]-=1
            if p["vida"] <= 0: partes.remove(p); continue
            a = min(255, p["vida"]*3)
            s = pygame.Surface((p["tam"]*2,p["tam"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["cor"],a), (p["tam"],p["tam"]), p["tam"])
            tela.blit(s, (int(p["x"])-p["tam"], int(p["y"])-p["tam"]))

        # Título modo
        pulse = abs(math.sin(t*3))
        cor_p = tuple(min(255,int(cor_m[k]*(0.65+pulse*0.35))) for k in range(3))
        titulo_modo = NOMES_MODO.get(modo, modo.upper())
        _glow_text(tela, fonte_titulo, titulo_modo, cor_p,
                   (LARGURA//2, 68+slide), centro=True, glow_r=6, glow_cor=cor_m)

        # Subtítulo
        SUB_Y = 148+slide
        if eh_recorde:
            pulse_rec = abs(math.sin(t*5))
            cor_rec = tuple(min(255,int(DOURADO[k]*(0.65+pulse_rec*0.35))) for k in range(3))
            _glow_text(tela, fonte_med, "✦  NOVO RECORDE DO MODO!  ✦", cor_rec,
                       (LARGURA//2, SUB_Y), centro=True, glow_r=4, glow_cor=LARANJA)
        elif posicao:
            _glow_text(tela, fonte_med, f"⬆  TOP {posicao} DO MODO!", VERDE_NEO,
                       (LARGURA//2, SUB_Y), centro=True, glow_r=3)

        # ── Painel esquerdo — pontuação principal ─────────────────
        GAP_P  = 14; PAINEL_Y = 190 + slide; PAINEL_H = 260
        lp_w   = 420; lp_x = LARGURA//2 - lp_w - GAP_P//2
        _rect_alpha(tela, (0,0,0), 80, (lp_x+4, PAINEL_Y+4, lp_w, PAINEL_H), raio=12)
        _painel_cyber(tela, (lp_x, PAINEL_Y, lp_w, PAINEL_H), cor_borda=cor_m, alpha=235, borda=2, raio=12)

        lbl_pf = fonte_mini.render("PONTUAÇÃO FINAL", True, CYBER_DIM)
        tela.blit(lbl_pf, (lp_x + lp_w//2 - lbl_pf.get_width()//2, PAINEL_Y+10))
        pygame.draw.line(tela, cor_m, (lp_x+16, PAINEL_Y+30), (lp_x+lp_w-16, PAINEL_Y+30), 1)

        cor_pts = DOURADO if eh_recorde else BRANCO
        s_pts   = fonte_grande.render(f"{pontos:,}".replace(",","."), True, cor_pts)
        tela.blit(s_pts, (lp_x + lp_w//2 - s_pts.get_width()//2, PAINEL_Y+44))

        if extra_info:
            s_ex = fonte_peq.render(extra_info, True, cor_m)
            tela.blit(s_ex, (lp_x + lp_w//2 - s_ex.get_width()//2, PAINEL_Y + 120))

        # Posição no ranking do modo
        if posicao:
            cor_pos = DOURADO if posicao == 1 else (200,200,210) if posicao==2 else (200,120,50)
            pos_s = fonte_hud.render(f"#{posicao} DO MODO", True, cor_pos)
            tela.blit(pos_s, (lp_x + lp_w//2 - pos_s.get_width()//2, PAINEL_Y + 160))

        # ── Painel direito — top 5 ─────────────────────────────────
        rp_w  = 310; rp_x = LARGURA//2 + GAP_P//2
        _rect_alpha(tela, (0,0,0), 80, (rp_x+4, PAINEL_Y+4, rp_w, PAINEL_H), raio=12)
        _painel_cyber(tela, (rp_x, PAINEL_Y, rp_w, PAINEL_H), cor_borda=CYBER_BORDA, alpha=225, borda=2, raio=12)
        lbl_t5 = fonte_mini.render("RANKING DO MODO", True, CYBER_DIM)
        tela.blit(lbl_t5, (rp_x + rp_w//2 - lbl_t5.get_width()//2, PAINEL_Y+10))
        pygame.draw.line(tela, CYBER_BORDA, (rp_x+16, PAINEL_Y+30), (rp_x+rp_w-16, PAINEL_Y+30), 1)

        top = dados_modos.get(modo, [])
        cores_rank = [DOURADO, (200,200,210), (200,120,50), CYBER_TEXTO, CYBER_DIM]
        if not top:
            s_np = fonte_mini.render("Sem partidas ainda", True, CINZA)
            tela.blit(s_np, (rp_x+16, PAINEL_Y+44))
        for ri, ent in enumerate(top[:5]):
            cor_r = cores_rank[min(ri,4)]
            ry = PAINEL_Y + 40 + ri * 40
            # Highlight da posição atual
            if ent["pontos"] == pontos:
                _rect_alpha(tela, cor_r, 30, (rp_x+8, ry-2, rp_w-16, 36), raio=5)
            prefix = ["1.", "2.", "3.", "4.", "5."][ri]
            p_s = fonte_mini.render(f"{prefix}", True, cor_r)
            v_s = fonte_ranking.render(f"{ent['pontos']:,}".replace(",","."), True, cor_r)
            ex_s = fonte_mini.render(ent.get("extra",""), True, CINZA)
            tela.blit(p_s, (rp_x+14, ry+4))
            tela.blit(v_s, (rp_x+40, ry))
            tela.blit(ex_s, (rp_x + rp_w - ex_s.get_width() - 14, ry+4))
            if ri < len(top)-1 and ri < 4:
                _linha_alpha(tela, CINZA_ESC, 30, (rp_x+12, ry+36), (rp_x+rp_w-12, ry+36))

        # ── Botão jogar novamente ────────────────────────────────
        by_btn  = PAINEL_Y + PAINEL_H + 18
        bw_btn  = 340; bh_btn = 52
        bx_btn  = LARGURA//2 - bw_btn//2
        pulse_btn = abs(math.sin(t*3))
        cor_btn = tuple(min(255, int(cor_m[k]*(0.55+pulse_btn*0.45))) for k in range(3))
        _rect_alpha(tela, (0,0,0), 80, (bx_btn+4, by_btn+4, bw_btn, bh_btn), raio=10)
        _painel_cyber(tela, (bx_btn, by_btn, bw_btn, bh_btn), cor_borda=cor_btn, alpha=220, borda=2, raio=10)
        _glow_text(tela, fonte_med, "JOGAR NOVAMENTE", cor_btn,
                   (LARGURA//2, by_btn+bh_btn//2), centro=True, glow_r=2)

        _glow_text(tela, fonte_mini, "ENTER — jogar novamente     ESC — menu",
                   CYBER_DIM, (LARGURA//2, ALTURA-16), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN: return "jogar"
                if ev.key == pygame.K_ESCAPE: return "menu"



# ================================================================
# TELA DE TUTORIAL — INTERATIVA COM PÁGINAS
# ================================================================
def tela_tutorial(dados: dict) -> None:
    """Tutorial interativo com páginas ilustradas."""
    PAGINAS = [
        {
            "titulo": "BEM-VINDO AO SNAKE BYTEFORGE",
            "cor": VERDE_NEO,
            "itens": [
                ("OBJETIVO", "Coma macas para crescer e aumentar sua pontuacao."),
                ("CONTROLES", "W A S D  ou  Setas do teclado para mover a cobra."),
                ("CUIDADO",   "Nao bata nas paredes nem no seu proprio corpo!"),
                ("INIMIGOS",  "Cobras IA tentarao te eliminar a cada nivel."),
            ],
            "icone": "cobra",
        },
        {
            "titulo": "ITENS E POWER-UPS",
            "cor": DOURADO,
            "itens": [
                ("MACA NORMAL",  "Vale 10 pontos x seu multiplicador de combo."),
                ("MACA DOURADA", "Ativa o modo POWER por 5s — voce fica invencivel!"),
                ("POWER-UP x2~x5","Diamante colorido: multiplica pontos por 2, 3, 4 ou 5!"),
                ("COMBO",        "Comer macas seguidas aumenta seu multiplicador de pontos."),
            ],
            "icone": "maca",
        },
        {
            "titulo": "NIVEIS E INIMIGOS",
            "cor": VERMELHO,
            "itens": [
                ("NIVEIS",       "A cada 250 pts sobem de nivel — mais rapido e mais inimigos."),
                ("AGRESSIVA",    "Persegue voce diretamente. Perigo constante."),
                ("EMBOSCADORA",  "Tenta prever seu caminho e cortar sua rota."),
                ("COOPERATIVA",  "Trabalha em equipe para te cercar."),
            ],
            "icone": "inimigo",
        },
        {
            "titulo": "MODOS DE JOGO",
            "cor": MAGENTA,
            "itens": [
                ("CLASSICO",     "Modo principal com niveis e IA crescente."),
                ("ENDLESS",      "Sem fim! Velocidade cresce infinitamente."),
                ("HARDCORE",     "Uma vida, sem perdao. Game over = tudo perdido."),
                ("TIME ATTACK",  "90 segundos para pontuar o maximo possivel!"),
                ("BOSS RUSH",    "Enfrente 4 chefes gigantes em sequencia."),
                ("MULTIPLAYER",  "P1 WASD vs P2 Setas — elimine o rival!"),
            ],
            "icone": "modos",
        },
        {
            "titulo": "DICAS AVANCADAS",
            "cor": CIANO,
            "itens": [
                ("MOEDAS",       "Ganhe moedas com pontos e desbloqueie novas skins."),
                ("SKINS ANIMAIS","Leao, Cobra Real, Dragao e Tigre com visuais unicos!"),
                ("SALVO AUTO",   "O jogo salva automaticamente seu progresso."),
                ("DICA PRO",     "Use o modo POWER para eliminar inimigos e ganhar bonus!"),
            ],
            "icone": "dica",
        },
    ]

    pagina_atual = 0
    t = 0.0
    anim_in = 0.0
    anim_pagina = 0.0

    def _desenhar_icone_tutorial(cx, cy, tipo, t_anim):
        """Desenha ícone animado ilustrativo."""
        pulso = abs(math.sin(t_anim * 2))
        if tipo == "cobra":
            corpo = [(cx + i*10 - 40, cy + int(math.sin((i + t_anim*3)*0.8)*12))
                     for i in range(10)]
            for i, p in enumerate(corpo):
                cor = _hsv((i*36 + t_anim*60) % 360, 0.9, 0.8)
                pygame.draw.circle(tela, cor, p, max(2, 8-i//2))
        elif tipo == "maca":
            # Maçã pulsante
            r = int(28 + pulso*5)
            pygame.draw.circle(tela, VERMELHO, (cx, cy+4), r)
            pygame.draw.circle(tela, (255,100,100), (cx-r//3, cy-r//3), r//3)
            pygame.draw.line(tela, (100,60,10), (cx, cy-r), (cx+4, cy-r-8), 3)
            pygame.draw.circle(tela, VERDE, (cx+4, cy-r-10), 6)
        elif tipo == "inimigo":
            cores = [VERMELHO, AZUL, ROXO, LARANJA, TEAL]
            for i in range(5):
                ang = t_anim*0.8 + i*1.26
                ix  = cx + int(math.cos(ang)*38)
                iy  = cy + int(math.sin(ang)*22)
                pygame.draw.circle(tela, cores[i], (ix, iy), 8)
                pygame.draw.circle(tela, BRANCO, (ix+2, iy-2), 3)
                pygame.draw.circle(tela, PRETO, (ix+2, iy-2), 2)
        elif tipo == "modos":
            # Hexágonos representando modos
            modos_cor = [VERDE_NEO, CIANO, VERMELHO, DOURADO, MAGENTA, LARANJA]
            for i, cor in enumerate(modos_cor):
                ang = t_anim*0.5 + i*(math.pi*2/6)
                ix  = cx + int(math.cos(ang)*36)
                iy  = cy + int(math.sin(ang)*22)
                pts = [(ix+int(math.cos(a)*10), iy+int(math.sin(a)*10))
                       for a in [k*math.pi/3 for k in range(6)]]
                pygame.draw.polygon(tela, cor, pts)
                pygame.draw.polygon(tela, BRANCO, pts, 1)
        elif tipo == "dica":
            # Estrela pulsante
            r_out = int(32 + pulso*6)
            r_in  = r_out // 2
            pts   = []
            for i in range(10):
                ang = t_anim*0.4 + i*math.pi/5 - math.pi/2
                r   = r_out if i%2==0 else r_in
                pts.append((cx+int(math.cos(ang)*r), cy+int(math.sin(ang)*r)))
            pygame.draw.polygon(tela, DOURADO, pts)
            pygame.draw.polygon(tela, LARANJA, pts, 2)

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.02
        anim_in    = min(1.0, anim_in + 0.07)
        anim_pagina= min(1.0, anim_pagina + 0.09)
        slide      = int((1.0-anim_in)**2 * -70)

        pg = PAGINAS[pagina_atual]
        cor_p = pg["cor"]

        # Título
        pulse_t = abs(math.sin(t*2.5))
        cor_tit = tuple(min(255, int(cor_p[k]*(0.75+pulse_t*0.25))) for k in range(3))
        _glow_text(tela, fonte_grande, pg["titulo"], cor_tit,
                   (LARGURA//2, 62 + slide), centro=True, glow_r=5, glow_cor=cor_p)

        # Indicador de página
        for pi in range(len(PAGINAS)):
            cx_i = LARGURA//2 + (pi - len(PAGINAS)//2) * 24
            cor_dot = cor_p if pi == pagina_atual else CINZA
            pygame.draw.circle(tela, cor_dot, (cx_i, 110 + slide), 6 if pi==pagina_atual else 4)

        # Painel principal
        pw = LARGURA - 120; ph = ALTURA - 200
        px = LARGURA//2 - pw//2; py = 128 + slide
        alpha_p = int(anim_pagina * 230)
        _painel_cyber(tela, (px, py, pw, ph), cor_borda=cor_p, alpha=alpha_p, borda=2, raio=12)

        # Ícone ilustrativo (lado direito)
        icone_x = px + pw - 120; icone_y = py + ph//2 - 30
        _desenhar_icone_tutorial(icone_x, icone_y, pg["icone"], t)

        # Itens de conteúdo
        conteudo_w = pw - 260
        for i, (chave, desc) in enumerate(pg["itens"]):
            iy = py + 24 + i * ((ph - 48) // max(1, len(pg["itens"])))
            alpha_item = min(255, int((anim_pagina - i*0.08) * 255))
            if alpha_item <= 0:
                continue
            # Badge da chave
            bw_k = 170
            _rect_alpha(tela, cor_p, min(180, alpha_item//2), (px+16, iy+2, bw_k, 32), raio=4)
            pygame.draw.rect(tela, cor_p, (px+16, iy+2, bw_k, 32), 1, border_radius=4)
            sk = fonte_mini.render(chave, True, BRANCO)
            sk.set_alpha(alpha_item)
            tela.blit(sk, (px+16+bw_k//2-sk.get_width()//2, iy+9))
            # Descrição
            sd = fonte_peq.render(desc, True, CYBER_TEXTO)
            sd.set_alpha(alpha_item)
            tela.blit(sd, (px+16+bw_k+16, iy+8))
            # Linha separadora
            if i < len(pg["itens"])-1:
                _linha_alpha(tela, CINZA_ESC, 40, (px+16, iy+40), (px+conteudo_w, iy+40))

        # Barra de progresso das páginas
        prog_w = pw - 32
        _rect_alpha(tela, CINZA_ESC, 100, (px+16, py+ph-14, prog_w, 6), raio=3)
        prog_fill = int(prog_w * (pagina_atual+1) / len(PAGINAS))
        _rect_alpha(tela, cor_p, 200, (px+16, py+ph-14, prog_fill, 6), raio=3)

        # Rodapé
        nav_txt = "← → ou A D  navegar     ENTER  próxima     ESC  fechar tutorial"
        if pagina_atual == len(PAGINAS) - 1:
            nav_txt = "← A  voltar     ENTER / ESC  começar a jogar!"
        _glow_text(tela, fonte_mini, nav_txt, CYBER_DIM,
                   (LARGURA//2, ALTURA-18), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                SOM_TUTORIAL_CLICK.play()
                if ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_SPACE):
                    if pagina_atual < len(PAGINAS)-1:
                        pagina_atual += 1; anim_pagina = 0.0
                    else:
                        return
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    if pagina_atual > 0:
                        pagina_atual -= 1; anim_pagina = 0.0
                elif ev.key == pygame.K_ESCAPE:
                    return


# ================================================================
# COBRA DECORATIVA DO MENU — MELHORADA
# ================================================================
class _CobradDemo:
    """Cobra decorativa com trail colorido no fundo do menu."""
    def __init__(self):
        self.corpo    = [(x, 14) for x in range(14, 4, -1)]
        self.direcao  = (1, 0)
        self.t        = 0
        self.pulso    = 0.0
        self.cor_h    = 120.0   # matiz para efeito arco-íris

    def atualizar(self):
        self.t     += 1
        self.pulso += 0.09
        self.cor_h  = (self.cor_h + 0.8) % 360

        if self.t % 3 == 0:
            x, y = self.corpo[0]; dx, dy = self.direcao
            if random.random() < 0.14:
                ops = [(1,0),(-1,0),(0,1),(0,-1)]
                ops = [(a,b) for a,b in ops if not(a==-dx and b==-dy)]
                self.direcao = random.choice(ops)
                dx, dy = self.direcao
            nova = (x+dx, y+dy)
            if not (1 < nova[0] < COLUNAS-2 and 1 < nova[1] < LINHAS-2):
                self.direcao = (-dx, -dy); dx,dy = self.direcao; nova = (x+dx, y+dy)
            self.corpo.insert(0, nova)
            if len(self.corpo) > 12: self.corpo.pop()

    def desenhar(self):
        pv = int(math.sin(self.pulso) * 20)
        for i, p in enumerate(self.corpo):
            if not (0 <= p[0] < COLUNAS and 0 <= p[1] < LINHAS): continue
            # Cor em gradiente dinâmico
            h_seg = (self.cor_h + i*25) % 360
            cor   = _hsv(h_seg, 0.9, 0.7)
            alpha = max(0, int(140 - i*11))
            fade  = max(0.2, 1.0 - i*0.08)
            cor_f = tuple(int(c*fade) for c in cor)
            s = pygame.Surface((GRID-4, GRID-4), pygame.SRCALPHA)
            pygame.draw.rect(s, (*cor_f, alpha), (0, 0, GRID-4, GRID-4), border_radius=5)
            tela.blit(s, (p[0]*GRID+2, p[1]*GRID+AREA_JOGO_Y+2))


# ================================================================
# MENU PRINCIPAL — CYBERPUNK APRIMORADO
# ================================================================
def menu(dados: dict) -> str:
    # RANKING removido do menu principal
    opcoes      = ["JOGAR", "TUTORIAL", "ESTATISTICAS", "SKINS", "SAIR"]
    opcao       = 0
    t           = 0.0
    cobra_demo  = _CobradDemo()
    anim_in     = 0.0

    # Cobras extras decorativas
    cobras_extra = [_CobradDemo() for _ in range(2)]
    for i, cb in enumerate(cobras_extra):
        cb.corpo   = [(x, 5 + i*8) for x in range(5, 0, -1)]
        cb.direcao = (1, 0)
        cb.cor_h   = 200 + i * 80

    overlay_img = None
    if IMAGEM_MENU:
        overlay_img = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay_img.fill((0, 0, 0, 175))

    # Dimensões fixas dos botões (calculadas uma vez)
    btn_jogar_w, btn_jogar_h = 420, 72
    btn_w, btn_h = 240, 52
    gap          = 18
    opcoes_sec   = opcoes[1:]   # ["ESTATISTICAS", "SKINS", "SAIR"]
    num_sec      = len(opcoes_sec)
    total_sec_w  = num_sec * btn_w + (num_sec - 1) * gap
    sec_start_x  = LARGURA//2 - total_sec_w//2
    sec_y        = ALTURA - btn_h - 48
    # JOGAR fica logo acima dos botões secundários, com gap de 16px
    btn_jogar_x  = LARGURA//2 - btn_jogar_w//2
    btn_jogar_y_base = sec_y - btn_jogar_h - 16

    MUSICA.tocar("menu")  # Música de fundo do menu

    while True:
        t += 0.02; anim_in = min(1.0, anim_in + 0.05)
        _fundo_cyber.atualizar()

        # — Posição do mouse
        mx, my = pygame.mouse.get_pos()

        # Calcula slide de entrada
        slide = int((1.0 - anim_in)**2 * -100)
        btn_jogar_y = btn_jogar_y_base + slide//2

        # Detecta hover do mouse por botão
        rect_jogar = pygame.Rect(btn_jogar_x, btn_jogar_y, btn_jogar_w, btn_jogar_h)
        rects_sec  = [
            pygame.Rect(sec_start_x + j*(btn_w+gap), sec_y, btn_w, btn_h)
            for j in range(num_sec)
        ]

        hover_jogar = rect_jogar.collidepoint(mx, my)
        hover_sec   = [r.collidepoint(mx, my) for r in rects_sec]

        # Atualiza opcao pelo hover do mouse (não força teclado)
        if hover_jogar:
            opcao = 0
        else:
            for j, h in enumerate(hover_sec):
                if h:
                    opcao = j + 1
                    break

        # — Fundo
        if IMAGEM_MENU:
            tela.blit(IMAGEM_MENU, (0, 0))
            tela.blit(overlay_img, (0, 0))
            for x in range(0,LARGURA,60):
                s=pygame.Surface((1,ALTURA),pygame.SRCALPHA); s.fill((*CIANO,8)); tela.blit(s,(x,0))
            for y in range(0,ALTURA,60):
                s=pygame.Surface((LARGURA,1),pygame.SRCALPHA); s.fill((*CIANO,8)); tela.blit(s,(0,y))
        else:
            _fundo_cyber.desenhar()

        # — Cobras decorativas
        cobra_demo.atualizar(); cobra_demo.desenhar()
        for cb in cobras_extra:
            cb.atualizar(); cb.desenhar()

        # — Título com slide de entrada
        cy_title = ALTURA//4 - 30 + slide

        # "SNAKE" com glow colorido pulsante
        pulse_t = abs(math.sin(t * 1.8))
        cor_snake = (
            int(VERDE_NEO[0] * (0.8 + pulse_t * 0.2)),
            int(VERDE_NEO[1] * (0.8 + pulse_t * 0.2)),
            int(VERDE_NEO[2] * (0.8 + pulse_t * 0.2)),
        )
        _glow_text(tela, fonte_titulo, "SNAKE", cor_snake,
                   (LARGURA//2, cy_title), centro=True, glow_r=6)

        # "BYTEFORGE" com cor magenta oscilante
        cor_byte = (
            int(MAGENTA[0] * (0.7 + pulse_t * 0.3)),
            int(MAGENTA[1] * (0.7 + pulse_t * 0.3)),
            int(MAGENTA[2] * (0.7 + pulse_t * 0.3)),
        )
        _glow_text(tela, fonte_titulo, "BYTEFORGE", cor_byte,
                   (LARGURA//2, cy_title+76), centro=True, glow_r=6, glow_cor=ROXO_BRILHO)



        # — Painel info rápida (canto esquerdo inferior)
        rec = dados["stats"]["pontuacao_maxima"]
        info_x = 20; info_y = 20
        _painel_cyber(tela, (info_x, info_y, 220, 140), cor_borda=DOURADO, alpha=190, raio=8)
        tela.blit(fonte_mini.render("RECORDE",       True, DOURADO),  (info_x+12, info_y+12))
        tela.blit(fonte_hud.render(f"{rec:,}".replace(",","."), True, BRANCO),   (info_x+12, info_y+34))
        tela.blit(fonte_mini.render("MOEDAS",        True, DOURADO),  (info_x+12, info_y+70))
        tela.blit(fonte_hud.render(str(dados["moedas"]), True, BRANCO),(info_x+12, info_y+90))

        # — Botão JOGAR (logo acima dos botões secundários)
        selecionado_jogar = (opcao == 0)
        _painel_cyber(tela, (btn_jogar_x, btn_jogar_y, btn_jogar_w, btn_jogar_h),
                      cor_borda=VERDE_NEO if selecionado_jogar else CYBER_BORDA, alpha=230, raio=14)
        if selecionado_jogar:
            pulse_s = abs(math.sin(t*4))
            hl = pygame.Surface((btn_jogar_w-20, btn_jogar_h-16), pygame.SRCALPHA)
            hl.fill((*VERDE_NEO, int(18 + pulse_s*22)))
            tela.blit(hl, (btn_jogar_x+10, btn_jogar_y+8))
            pygame.draw.rect(tela, VERDE_NEO, (btn_jogar_x+8, btn_jogar_y+10, 4, btn_jogar_h-20), border_radius=2)
            _rect_alpha(tela, VERDE_NEO, 60, (btn_jogar_x+btn_jogar_w-12, btn_jogar_y+10, 4, btn_jogar_h-20))
            _glow_text(tela, fonte_med, "JOGAR", VERDE_NEO,
                       (LARGURA//2 - fonte_med.size("JOGAR")[0]//2, btn_jogar_y + btn_jogar_h//2 - 20), glow_r=4)
        else:
            alpha_op = min(255, int(anim_in * 255))
            s_op = fonte_med.render("JOGAR", True, CYBER_DIM)
            s_op.set_alpha(alpha_op)
            tela.blit(s_op, (LARGURA//2 - s_op.get_width()//2, btn_jogar_y + btn_jogar_h//2 - 20))

        # — Botões secundários na parte inferior (ESTATISTICAS, SKINS, SAIR)
        for j, op_sec in enumerate(opcoes_sec):
            i_real      = j + 1
            bx          = sec_start_x + j * (btn_w + gap)
            by          = sec_y
            selecionado = (opcao == i_real)
            cor_borda_sec = CIANO if selecionado else CYBER_BORDA
            _painel_cyber(tela, (bx, by, btn_w, btn_h), cor_borda=cor_borda_sec, alpha=210, raio=10)
            if selecionado:
                pulse_s = abs(math.sin(t*4))
                hl2 = pygame.Surface((btn_w-16, btn_h-12), pygame.SRCALPHA)
                hl2.fill((*CIANO, int(15 + pulse_s*18)))
                tela.blit(hl2, (bx+8, by+6))
                pygame.draw.rect(tela, CIANO, (bx+6, by+6, 3, btn_h-12), border_radius=2)
                _glow_text(tela, fonte_peq, op_sec, CIANO,
                           (bx + btn_w//2 - fonte_peq.size(op_sec)[0]//2, by + btn_h//2 - 12), glow_r=2)
            else:
                alpha_op = min(255, int(anim_in * 255))
                s_sec = fonte_peq.render(op_sec, True, CYBER_DIM)
                s_sec.set_alpha(alpha_op)
                tela.blit(s_sec, (bx + btn_w//2 - s_sec.get_width()//2, by + btn_h//2 - s_sec.get_height()//2))

        # Hint controles
        hint = fonte_mini.render("↑↓  navegar    ENTER / CLIQUE  confirmar    ESC  sair", True, CINZA)
        tela.blit(hint, (LARGURA//2-hint.get_width()//2, ALTURA-20))

        # Cursor mão quando hover em botão
        qualquer_hover = hover_jogar or any(hover_sec)
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if qualquer_hover else pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    SOM_BOTAO.play(); opcao = (opcao-1) % len(opcoes)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    SOM_BOTAO.play(); opcao = (opcao+1) % len(opcoes)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    SOM_BOTAO.play()
                    if opcao == 0:
                        res = tela_selecao_modo(dados)
                        if res: return res
                    elif opcao == 1: tela_tutorial(dados)
                    elif opcao == 2: tela_estatisticas(dados)
                    elif opcao == 3: tela_skins(dados)
                    elif opcao == 4: pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                SOM_BOTAO.play()
                if rect_jogar.collidepoint(ev.pos):
                    res = tela_selecao_modo(dados)
                    if res: return res
                else:
                    for j, r in enumerate(rects_sec):
                        if r.collidepoint(ev.pos):
                            idx = j + 1
                            if idx == 1: tela_tutorial(dados)
                            elif idx == 2: tela_estatisticas(dados)
                            elif idx == 3: tela_skins(dados)
                            elif idx == 4: pygame.quit(); sys.exit()
                            break



# ================================================================
# TELA DE ESTATÍSTICAS PÓS-GAME OVER
# ================================================================
def tela_stats_partida(pontos: int, nivel: int, duracao_s: float,
                       stats_partida: dict, dados: dict) -> None:
    """Exibe estatísticas detalhadas após o game over antes da tela principal."""
    macas     = stats_partida.get("macas", 0)
    douradas  = stats_partida.get("douradas", 0)
    inimigos  = stats_partida.get("inimigos", 0)
    powerups  = stats_partida.get("powerups", 0)
    combo_max = stats_partida.get("combo_max", 0)
    moedas_ganhas = max(1, pontos // 20)

    t = 0.0; anim_in = 0.0

    # Contadores animados
    contadores = {
        "pontos":   {"alvo": pontos,        "atual": 0.0, "vel": max(1, pontos/80)},
        "macas":    {"alvo": macas,         "atual": 0.0, "vel": max(1, macas/60)},
        "inimigos": {"alvo": inimigos,      "atual": 0.0, "vel": max(1, inimigos/40)},
        "moedas":   {"alvo": moedas_ganhas, "atual": 0.0, "vel": max(1, moedas_ganhas/60)},
    }

    # ── Dimensões fixas (calculadas uma vez) ────────────────────────
    MARGEM   = 60          # margem lateral
    GAP      = 12          # espaço entre células
    COLS     = 3; ROWS = 2

    # Grid menor e centralizado verticalmente
    TITULO_H = 100         # espaço do título
    RODAPE_H = 140         # espaço do rodapé (moedas + powerups + timer)
    grid_w   = LARGURA - MARGEM * 2
    grid_h   = ALTURA - TITULO_H - RODAPE_H
    grid_y   = TITULO_H
    cell_w   = (grid_w - GAP * (COLS - 1)) // COLS
    cell_h   = (grid_h - GAP * (ROWS - 1)) // ROWS

    timer = 6.0
    inicio = time.time()

    # Overlay escuro pré-criado para sobre a imagem de fundo
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))

    while True:
        t += 0.02
        anim_in = min(1.0, anim_in + 0.07)
        slide   = int((1.0 - anim_in)**2 * -60)
        timer   = max(0.0, timer - 0.016)

        # Animar contadores
        for c in contadores.values():
            if c["atual"] < c["alvo"]:
                c["atual"] = min(c["alvo"], c["atual"] + c["vel"])

        # ── FUNDO: imagem do menu + overlay escuro ───────────────────
        if IMAGEM_MENU:
            tela.blit(IMAGEM_MENU, (0, 0))
            tela.blit(overlay, (0, 0))
            # Grade ciano sutil
            for gx in range(0, LARGURA, 60):
                s = pygame.Surface((1, ALTURA), pygame.SRCALPHA)
                s.fill((*CIANO, 6)); tela.blit(s, (gx, 0))
            for gy in range(0, ALTURA, 60):
                s = pygame.Surface((LARGURA, 1), pygame.SRCALPHA)
                s.fill((*CIANO, 6)); tela.blit(s, (0, gy))
        else:
            _fundo_cyber.atualizar(); _fundo_cyber.desenhar()

        # ── TÍTULO ──────────────────────────────────────────────────
        pulse_r = abs(math.sin(t * 4))
        cor_tit = (min(255, int(220 + pulse_r*35)),
                   int(80 + pulse_r*80),
                   int(20*(1-pulse_r)))
        _glow_text(tela, fonte_titulo, "ESTATISTICAS DA PARTIDA", cor_tit,
                   (LARGURA//2, 42 + slide), centro=True, glow_r=6, glow_cor=LARANJA)

        # ── PAINEL EXTERNO DO GRID ───────────────────────────────────
        gy_atual = grid_y + slide
        _rect_alpha(tela, (0,0,0), 80,
                    (MARGEM+4, gy_atual+4, grid_w, grid_h), raio=14)
        _painel_cyber(tela, (MARGEM, gy_atual, grid_w, grid_h),
                      cor_borda=VERMELHO, alpha=220, borda=2, raio=14)

        # ── CÉLULAS 3×2 ──────────────────────────────────────────────
        stats_grid = [
            ("PONTUACAO",    f"{int(contadores['pontos']['atual']):,}".replace(",","."), DOURADO,   fonte_grande),
            ("NIVEL",         str(nivel),                                                 VERDE_NEO, fonte_grande),
            ("TEMPO",         _fmt_tempo(int(duracao_s)),                                 CIANO,     fonte_grande),
            ("MACAS COMIDAS", f"{int(contadores['macas']['atual'])}",                    VERMELHO,  fonte_grande),
            ("INIMIGOS",      f"{int(contadores['inimigos']['atual'])}",                 LARANJA,   fonte_grande),
            ("COMBO MAX",     f"x{combo_max}",                                            ROSA,      fonte_grande),
        ]

        for idx, (label, valor, cor_c, fonte_v) in enumerate(stats_grid):
            col = idx % COLS
            row = idx // COLS
            cx_c = MARGEM + col * (cell_w + GAP)
            cy_c = gy_atual + row * (cell_h + GAP)

            # Fundo pulsante da célula
            pulse_c = abs(math.sin(t * 2.5 + idx * 0.8))
            _rect_alpha(tela, cor_c, int(25 + pulse_c*25),
                        (cx_c+2, cy_c+2, cell_w-4, cell_h-4), raio=10)
            pygame.draw.rect(tela, cor_c,
                             (cx_c+2, cy_c+2, cell_w-4, cell_h-4),
                             2, border_radius=10)

            # Label (pequeno, topo da célula)
            sl = fonte_mini.render(label, True, CYBER_DIM)
            tela.blit(sl, (cx_c + cell_w//2 - sl.get_width()//2, cy_c + 10))

            # Valor (centralizado verticalmente na célula)
            sv = fonte_v.render(valor, True, cor_c)
            if sv.get_width() > cell_w - 20:
                sv = fonte_med.render(valor, True, cor_c)
            if sv.get_width() > cell_w - 20:
                sv = fonte_hud.render(valor, True, cor_c)
            tela.blit(sv, (cx_c + cell_w//2 - sv.get_width()//2,
                           cy_c + cell_h//2 - sv.get_height()//2 + 10))

        # ── RODAPÉ ──────────────────────────────────────────────────
        rod_y = gy_atual + grid_h + 12

        # Moedas ganhas — destaque grande e pulsante
        pulse_m  = abs(math.sin(t * 4))
        moedas_s = fonte_med.render(
            f"+{int(contadores['moedas']['atual'])} moedas ganhas!", True, DOURADO)
        moedas_s.set_alpha(int(190 + pulse_m*65))
        tela.blit(moedas_s, (LARGURA//2 - moedas_s.get_width()//2, rod_y))

        # Power-ups e maçãs douradas — linha menor abaixo
        pw_s = fonte_peq.render(
            f"Power-ups coletados: {powerups}   |   Macas douradas: x{douradas}",
            True, CYBER_DIM)
        tela.blit(pw_s, (LARGURA//2 - pw_s.get_width()//2, rod_y + 42))

        # Timer
        timer_s = fonte_mini.render(
            f"Continuando em {int(timer)+1}s...   ENTER / ESC para ir agora",
            True, CYBER_DIM)
        tela.blit(timer_s, (LARGURA//2 - timer_s.get_width()//2, ALTURA - 26))

        # Barra do timer
        tw = 340
        _rect_alpha(tela, CINZA_ESC, 100,
                    (LARGURA//2-tw//2, ALTURA-10, tw, 6), raio=3)
        _rect_alpha(tela, VERDE_NEO, 220,
                    (LARGURA//2-tw//2, ALTURA-10, int(tw*(timer/6.0)), 6), raio=3)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    return

        if timer <= 0:
            return


# ================================================================
# GAME OVER — CYBERPUNK APRIMORADO
# ================================================================
def game_over_screen(pontos: int, nivel: int, dados: dict,
                     stats_partida: dict, duracao_s: float) -> str:
    if duracao_s > dados.get("partida_mais_longa_s", 0):
        dados["partida_mais_longa_s"] = int(duracao_s)

    recorde_anterior = dados["stats"]["pontuacao_maxima"]
    registrar_partida(dados, pontos, nivel, duracao_s, stats_partida)
    recorde      = dados["stats"]["pontuacao_maxima"]
    novo_recorde = pontos >= recorde_anterior and pontos > 0
    top10        = any(e["pontos"] == pontos for e in dados["ranking"][:10])
    moedas_ganhas = max(1, pontos // 20)

    t = 0.0; anim_in = 0.0
    parts_go: list = []
    for _ in range(70):
        cx_p = random.uniform(LARGURA*0.25, LARGURA*0.75)
        cy_p = random.uniform(ALTURA*0.25, ALTURA*0.65)
        parts_go.append({
            "x": cx_p, "y": cy_p,
            "vx": random.uniform(-4, 4), "vy": random.uniform(-5, 0.5),
            "vida": random.randint(50, 110),
            "cor":  random.choice([VERMELHO, LARANJA, ROSA, DOURADO, (255,100,60)]),
            "tam":  random.randint(2, 6),
        })

    while True:
        _fundo_cyber.atualizar(); _fundo_cyber.desenhar()
        t += 0.025; anim_in = min(1.0, anim_in + 0.055)
        slide = int((1.0 - anim_in)**2 * -90)

        # Partículas
        for p in parts_go[:]:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=0.12; p["vida"]-=1
            if p["vida"] <= 0: parts_go.remove(p); continue
            a = min(255, p["vida"]*3)
            s = pygame.Surface((p["tam"]*2, p["tam"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["cor"], a), (p["tam"], p["tam"]), p["tam"])
            tela.blit(s, (int(p["x"])-p["tam"], int(p["y"])-p["tam"]))

        # Título GAME OVER
        pulse_r = abs(math.sin(t * 4))
        cor_go = (min(255, int(210 + pulse_r*45)), int(25*(1-pulse_r)), int(25*(1-pulse_r)))
        _glow_text(tela, fonte_titulo, "GAME OVER", cor_go,
                   (LARGURA//2, 72 + slide), centro=True, glow_r=7, glow_cor=LARANJA)

        # Subtítulo
        SUB_Y = 148 + slide
        if novo_recorde:
            pulse_nr = abs(math.sin(t*5))
            cor_nr = tuple(min(255, int(DOURADO[k]*(0.65+pulse_nr*0.35))) for k in range(3))
            _glow_text(tela, fonte_med, "✦  NOVO RECORDE!  ✦", cor_nr,
                       (LARGURA//2, SUB_Y), centro=True, glow_r=5, glow_cor=LARANJA)
        elif top10:
            _glow_text(tela, fonte_med, "⬆  ENTROU NO TOP 10!", VERDE_NEO,
                       (LARGURA//2, SUB_Y), centro=True, glow_r=3)

        # ── Layout: painel esquerdo (stats) + painel direito (mini-stats) ──
        cor_borda_p = DOURADO if novo_recorde else VERMELHO
        MARGEM      = 60
        GAP_P       = 16
        PAINEL_Y    = 188 + slide
        PAINEL_H    = 300

        # Painel esquerdo — resultados principais
        lp_w = 520
        lp_x = LARGURA//2 - lp_w - GAP_P//2
        _rect_alpha(tela, (0,0,0), 80, (lp_x+4, PAINEL_Y+4, lp_w, PAINEL_H), raio=12)
        _painel_cyber(tela, (lp_x, PAINEL_Y, lp_w, PAINEL_H),
                      cor_borda=cor_borda_p, alpha=230, borda=2, raio=12)

        lbl_res = fonte_mini.render("RESULTADO", True, CYBER_DIM)
        tela.blit(lbl_res, (lp_x + lp_w//2 - lbl_res.get_width()//2, PAINEL_Y + 10))
        pygame.draw.line(tela, cor_borda_p, (lp_x+16, PAINEL_Y+30), (lp_x+lp_w-16, PAINEL_Y+30), 1)

        linhas_res = [
            ("PONTUAÇÃO", f"{pontos:,}".replace(",","."), DOURADO if novo_recorde else BRANCO, fonte_grande),
            ("NÍVEL",     str(nivel),                     VERDE_NEO,                            fonte_med),
            ("RECORDE",   f"{recorde:,}".replace(",","."), DOURADO,                             fonte_med),
            ("MOEDAS",    f"+{moedas_ganhas}",             (255,210,0),                         fonte_med),
            ("TEMPO",     _fmt_tempo(int(duracao_s)),      CINZA,                               fonte_peq),
        ]
        row_h = (PAINEL_H - 36) // len(linhas_res)
        for i, (label, valor, cor_v, f_val) in enumerate(linhas_res):
            ry = PAINEL_Y + 36 + i * row_h
            # Barra indicadora colorida
            pygame.draw.rect(tela, cor_v, (lp_x+12, ry+4, 3, row_h-8), border_radius=2)
            sl = fonte_mini.render(label, True, CYBER_DIM)
            sv = f_val.render(valor, True, cor_v)
            tela.blit(sl, (lp_x+24, ry + 2))
            tela.blit(sv, (lp_x + lp_w - sv.get_width() - 20, ry))
            if i < len(linhas_res)-1:
                _linha_alpha(tela, CINZA_ESC, 35, (lp_x+16, ry+row_h-1), (lp_x+lp_w-16, ry+row_h-1))

        # Painel direito — mini stats 2×2
        rp_w = 260
        rp_x = LARGURA//2 + GAP_P//2
        _rect_alpha(tela, (0,0,0), 80, (rp_x+4, PAINEL_Y+4, rp_w, PAINEL_H), raio=12)
        _painel_cyber(tela, (rp_x, PAINEL_Y, rp_w, PAINEL_H),
                      cor_borda=CYBER_BORDA, alpha=220, borda=2, raio=12)
        lbl_st = fonte_mini.render("ESTATÍSTICAS", True, CYBER_DIM)
        tela.blit(lbl_st, (rp_x + rp_w//2 - lbl_st.get_width()//2, PAINEL_Y+10))
        pygame.draw.line(tela, CYBER_BORDA, (rp_x+16, PAINEL_Y+30), (rp_x+rp_w-16, PAINEL_Y+30), 1)

        mini_info = [
            ("MAÇAS",    str(stats_partida.get("macas",0)),          VERMELHO),
            ("INIMIGOS", str(stats_partida.get("inimigos",0)),        LARANJA),
            ("COMBO",    f"x{stats_partida.get('combo_max',0)}",      ROSA),
            ("POWERS",   str(stats_partida.get("powerups",0)),        CIANO),
        ]
        ms_row_h = (PAINEL_H - 36) // 2
        for mi, (title, val, cor_card) in enumerate(mini_info):
            col_i = mi % 2; row_i = mi // 2
            mx = rp_x + 10 + col_i * (rp_w//2 - 6)
            my = PAINEL_Y + 36 + row_i * ms_row_h
            cell_w = rp_w//2 - 14; cell_h = ms_row_h - 8
            _painel_cyber(tela, (mx, my, cell_w, cell_h), cor_borda=cor_card, alpha=190, borda=1, raio=6)
            tl = fonte_mini.render(title, True, CYBER_DIM)
            vl = fonte_hud.render(val, True, cor_card)
            tela.blit(tl, (mx + cell_w//2 - tl.get_width()//2, my+5))
            tela.blit(vl, (mx + cell_w//2 - vl.get_width()//2, my+20))

        # ── Botão jogar novamente ────────────────────────────────
        by_btn  = PAINEL_Y + PAINEL_H + 20
        bw_btn  = 340; bh_btn = 52
        bx_btn  = LARGURA//2 - bw_btn//2
        pulse_btn = abs(math.sin(t*3))
        cor_btn = tuple(min(255, int(VERDE_NEO[k]*(0.55+pulse_btn*0.45))) for k in range(3))
        _rect_alpha(tela, (0,0,0), 80, (bx_btn+4, by_btn+4, bw_btn, bh_btn), raio=10)
        _painel_cyber(tela, (bx_btn, by_btn, bw_btn, bh_btn), cor_borda=cor_btn, alpha=220, borda=2, raio=10)
        _glow_text(tela, fonte_med, "JOGAR NOVAMENTE", cor_btn,
                   (LARGURA//2, by_btn + bh_btn//2), centro=True, glow_r=2)

        _glow_text(tela, fonte_mini, "ENTER — jogar    R — ranking    ESC — menu",
                   CYBER_DIM, (LARGURA//2, ALTURA - 16), centro=True)

        pygame.display.update(); clock.tick(FPS_RENDER)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN: return "jogar"
                if ev.key == pygame.K_ESCAPE: return "menu"
                if ev.key == pygame.K_r:      tela_ranking(dados)


# ================================================================
# JOGO PRINCIPAL
# ================================================================
def jogo(dados: dict):
    skin  = dados.get("skin_ativa","classico")
    snake = Snake(skin=skin)
    foods = Foods()
    nivel = 1; pontos = 0; combo = 0; combo_timer = 0; multiplicador = 1; multi_nivel = 1
    inimigos: list = []

    multi_pw_valor: int   = 1
    multi_pw_expira: float= 0.0
    multi_pw_expirou: bool= False

    sp = {"macas":0,"douradas":0,"inimigos":0,"powerups":0,"combo_max":0}

    dificuldade_din.__init__()
    inicio_partida = time.time()

    def spawn_inimigos():
        nonlocal inimigos
        inimigos = criar_inimigos(nivel, snake.corpo)

    spawn_inimigos()

    MUSICA.tocar(MODO_CLASSICO)  # Música de fundo do modo Clássico (loop até morrer)
    acumulador  = 0.0; ultimo_frame = time.time(); tick_logica = 0

    pausado = False

    while True:
        agora       = time.time(); delta = min(agora-ultimo_frame,0.1); ultimo_frame = agora
        fps_logica  = (FPS_BASE+(nivel-1)*(FPS_MAX-FPS_BASE)/9)*(1+dificuldade_din.velocidade_extra())
        intervalo   = 1.0/fps_logica
        acumulador += delta

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_p:
                    pausado = not pausado
                    if pausado:
                        MUSICA.set_volume(0.08)   # música bem baixa no pause
                    else:
                        MUSICA.set_volume(0.35)   # volume normal ao retomar
                        ultimo_frame = time.time()  # evita salto de acumulador
                        acumulador = 0.0
                elif not pausado:
                    if   ev.key in(pygame.K_UP,   pygame.K_w) and snake.direcao!=(0, 1): snake.prox_direcao=(0,-1)
                    elif ev.key in(pygame.K_DOWN, pygame.K_s) and snake.direcao!=(0,-1): snake.prox_direcao=(0, 1)
                    elif ev.key in(pygame.K_LEFT, pygame.K_a) and snake.direcao!=(1, 0): snake.prox_direcao=(-1,0)
                    elif ev.key in(pygame.K_RIGHT,pygame.K_d) and snake.direcao!=(-1,0): snake.prox_direcao=( 1,0)
                    elif ev.key==pygame.K_ESCAPE: MUSICA.parar(); return "menu"

        resultado_loop = None
        if not pausado:
            while acumulador>=intervalo and not resultado_loop:
                acumulador -= intervalo; tick_logica += 1
                snake.mover()
                if snake.power and agora>snake.power_time: snake.power=False
    
                combo_timer -= 1
                if combo_timer<=0: combo=multiplicador=multi_nivel=1
    
                if multi_pw_valor>1 and agora>=multi_pw_expira:
                    multi_pw_valor=1; multi_pw_expirou=True
    
                if tick_logica%10==0:
                    dificuldade_din.registrar(pontos); dificuldade_din.atualizar()
    
                novo_nivel=nivel_para_pontos(pontos)
                if novo_nivel>nivel:
                    nivel=novo_nivel; spawn_inimigos()
                    SOM_NIVEL_UP.play()  # Som especial de nível
                    MUSICA.acelerar(nivel)  # Acelera a música conforme o nível
                    # Efeito visual de nível — partículas em cascata
                    for gx in range(0, COLUNAS, 4):
                        adicionar_particulas(gx, random.randint(0, LINHAS-1),
                                            VERDE_NEO, 3)
                        adicionar_particulas(gx, random.randint(0, LINHAS-1),
                                            DOURADO, 2)
                    flash(VERDE_NEO, 80)
                    animacao_level_up(nivel,[b.personalidade for b in inimigos])
                    fps_logica=(FPS_BASE+(nivel-1)*(FPS_MAX-FPS_BASE)/9); intervalo=1.0/fps_logica
                    excluir_lv=set(snake.corpo)|set(foods.normais)
                    foods.ajustar_macas_nivel(nivel, excluir_lv)
    
                cab=snake.corpo[0]
    
                if cab in foods.normais:
                    snake.crescer(); foods.normais.remove(cab)
                    excluir=set(snake.corpo)|set(foods.normais)
                    foods.normais.append(foods.nova_comida(excluir))
                    foods.tentar_spawn_multi(excluir|set(foods.normais))
                    combo+=1; combo_timer=int(fps_logica*3); multiplicador=1+combo//3
                    mult_total=multiplicador*multi_pw_valor; pontos+=10*mult_total
                    sp["macas"]+=1; sp["combo_max"]=max(sp["combo_max"],combo)
                    SOM_COMER.play(); adicionar_particulas(cab[0],cab[1],VERMELHO)
    
                if foods.dourada and cab==foods.dourada:
                    snake.power=True; snake.power_time=agora+5; foods.dourada=None
                    pontos+=50*multiplicador*multi_pw_valor; sp["douradas"]+=1
                    SOM_POWER.play(); adicionar_particulas(cab[0],cab[1],DOURADO,12); flash(DOURADO,80)
                    # Respawna nova maca dourada imediatamente
                    excluir_d=set(snake.corpo)|set(foods.normais)
                    foods.dourada=foods.nova_comida(excluir_d)
    
                # Garante que a maca dourada sempre existe (caso roubada por inimigo)
                if foods.dourada is None and tick_logica % 50 == 0:
                    excluir_d=set(snake.corpo)|set(foods.normais)
                    foods.dourada=foods.nova_comida(excluir_d)
    
                if foods.multi_pw and cab==foods.multi_pw[0]:
                    pos,valor=foods.multi_pw; foods.multi_pw=None
                    multi_pw_valor=valor; multi_pw_expira=agora+MULTI_DURACAO
                    multi_pw_expirou=False; sp["powerups"]+=1
                    SOM_POWERUP_PEGAR.play()  # Som especial de power-up
                    # Efeito visual de power-up — explosão radial colorida
                    cor_pw = MULTI_CORES.get(valor, CIANO)
                    for ang in range(0, 360, 30):
                        rad = math.radians(ang)
                        gx  = max(0, min(COLUNAS-1, pos[0]+int(math.cos(rad)*3)))
                        gy  = max(0, min(LINHAS-1,  pos[1]+int(math.sin(rad)*3)))
                        adicionar_particulas(gx, gy, cor_pw, 8)
                    adicionar_particulas(pos[0],pos[1],BRANCO,10)
                    flash(cor_pw, 120)
    
                for bot in inimigos:
                    outros=[b.corpo for b in inimigos if b is not bot]+[snake.corpo]
                    bot.nivel_jogo=nivel
                    bot.mover(foods.normais,snake.corpo[0],outros,
                              player_direcao=snake.direcao,player_power=snake.power,
                              dourada_pos=foods.dourada,aliados=inimigos)
    
                if foods.dourada:
                    for bot in inimigos:
                        if bot.corpo and bot.corpo[0]==foods.dourada:
                            bot.power=True; bot.power_time=agora+6; foods.dourada=None
                            SOM_POWER.play()
                            adicionar_particulas(bot.corpo[0][0],bot.corpo[0][1],DOURADO,14)
                            flash(LARANJA,70); break
    
                bots_remover=[]
                for i,bot in enumerate(inimigos):
                    cbx,cby=bot.corpo[0]
                    if not(0<=cbx<COLUNAS and 0<=cby<LINHAS):
                        bots_remover.append(i)
                        adicionar_particulas(max(0,min(COLUNAS-1,cbx)),max(0,min(LINHAS-1,cby)),bot.cor,10); continue
                    if snake.corpo[0] in bot.corpo[1:] or snake.corpo[0]==bot.corpo[0]:
                        if snake.power and not bot.power:
                            bots_remover.append(i); pontos+=30*multiplicador*multi_pw_valor
                            sp["inimigos"]+=1; SOM_COMER.play()
                            adicionar_particulas(cbx,cby,bot.cor,10)
                        else: flash(VERMELHO,180); resultado_loop=("gameover",pontos,nivel)
                    elif bot.corpo[0] in snake.corpo:
                        if bot.power: flash(VERMELHO,180); resultado_loop=("gameover",pontos,nivel)
                        else:
                            bots_remover.append(i); pontos+=30*multiplicador*multi_pw_valor
                            sp["inimigos"]+=1; SOM_COMER.play()
                            adicionar_particulas(cbx,cby,bot.cor,10)
    
                for i,bot in enumerate(inimigos):
                    if not bot.power or i in bots_remover: continue
                    for j,outro in enumerate(inimigos):
                        if j==i or j in bots_remover or outro.power: continue
                        if outro.corpo and (bot.corpo[0] in outro.corpo or outro.corpo[0] in bot.corpo):
                            bots_remover.append(j); pontos+=20*multiplicador*multi_pw_valor
                            adicionar_particulas(outro.corpo[0][0],outro.corpo[0][1],DOURADO,10)
                            SOM_COMER.play()
    
                for i in sorted(set(bots_remover),reverse=True):
                    if i<len(inimigos): inimigos.pop(i)
    
                if snake.colisao(): flash(VERMELHO,180); resultado_loop=("gameover",pontos,nivel)
    
        # Render
        tela.fill(PRETO); _desenhar_grid_cyber()
        foods.desenhar()
        for bot in inimigos: bot.desenhar()
        snake.desenhar()
        atualizar_particulas(delta if not pausado else 0); desenhar_particulas(); desenhar_flash()
        if multi_pw_expirou: SOM_MULTI_FIM.play(); multi_pw_expirou=False
        restante=max(0.0,multi_pw_expira-agora) if multi_pw_valor>1 else 0.0
        desenhar_hud(pontos,nivel,combo,multiplicador,snake,multi_nivel,
                     multi_pw_valor,restante,moedas=dados["moedas"])

        # ── Overlay de PAUSE ────────────────────────────────────────
        if pausado:
            ov = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            tela.blit(ov, (0, 0))
            t_pause = time.time()
            pulse_p = abs(math.sin(t_pause * 3))
            cor_p = tuple(int(CIANO[k]*(0.7+pulse_p*0.3)) for k in range(3))
            _glow_text(tela, fonte_titulo, "PAUSADO", cor_p,
                       (LARGURA//2, ALTURA//2 - 40), centro=True, glow_r=6)
            hint = fonte_peq.render("P  —  retomar     ESC  —  sair", True, CYBER_DIM)
            tela.blit(hint, (LARGURA//2 - hint.get_width()//2, ALTURA//2 + 40))
        pygame.display.update(); clock.tick(FPS_RENDER)

        if resultado_loop:
            SOM_EXPLOSAO.play()  # Explosão ao morrer
            flash(VERMELHO,200)
            MUSICA.game_over()  # Para a música do modo e toca o game over
            duracao = time.time()-inicio_partida
            # Efeito de explosão visual
            for _ in range(30):
                gx, gy = snake.corpo[0]
                adicionar_particulas(gx, gy, VERMELHO, 8)
                adicionar_particulas(gx, gy, LARANJA, 6)
                adicionar_particulas(gx, gy, DOURADO, 4)
            t0=time.time()
            while time.time()-t0<0.9:
                tela.fill(PRETO); _desenhar_grid_cyber()
                foods.desenhar()
                for bot in inimigos: bot.desenhar()
                snake.desenhar(); atualizar_particulas(0.016)
                desenhar_particulas(); desenhar_flash()
                pygame.display.update(); clock.tick(FPS_RENDER)
            return resultado_loop + (sp, duracao)


# ================================================================
# MAIN
# ================================================================
def main() -> None:
    VIDEO_INTRO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VID-20260512-WA0005.mp4")
    intro_video(VIDEO_INTRO)

    dados       = carregar_save()
    dados_modos = carregar_modos_save()

    # Garante campo extra de estatística
    if "partida_mais_longa_s" not in dados:
        dados["partida_mais_longa_s"] = 0

    global flash_alpha, particulas
    estado        = "menu"
    modo_atual    = MODO_CLASSICO
    resultado_jogo = None

    while True:
        if estado == "menu":
            acao = menu(dados)
            if acao == MODO_CLASSICO:
                modo_atual = MODO_CLASSICO
                estado = "jogo"
            elif acao in (MODO_ENDLESS, MODO_HARDCORE, MODO_TIME_ATTACK,
                          MODO_BOSS_RUSH, MODO_MULTI_VS):
                modo_atual = acao
                estado = "jogo_modo"
            # None ou ESC => loop again

        elif estado == "jogo":
            # Modo clássico original
            flash_alpha = 0; particulas = []
            resultado = jogo(dados)
            if isinstance(resultado, tuple) and resultado[0] == "gameover":
                _, pts, niv, sp, dur = resultado
                resultado_jogo = (pts, niv, sp, dur)
                estado = "gameover"
            else:
                estado = "menu"

        elif estado == "jogo_modo":
            flash_alpha = 0; particulas = []

            if modo_atual == MODO_ENDLESS:
                pts = jogo_endless(dados, dados_modos)
                registrar_placar_modo(dados_modos, MODO_ENDLESS, pts)
                acao = tela_resultado_modo(MODO_ENDLESS, pts, dados_modos)
                estado = "jogo_modo" if acao == "jogar" else "menu"

            elif modo_atual == MODO_HARDCORE:
                pts = jogo_hardcore(dados, dados_modos)
                registrar_placar_modo(dados_modos, MODO_HARDCORE, pts)
                acao = tela_resultado_modo(MODO_HARDCORE, pts, dados_modos)
                estado = "jogo_modo" if acao == "jogar" else "menu"

            elif modo_atual == MODO_TIME_ATTACK:
                pts = jogo_time_attack(dados, dados_modos)
                registrar_placar_modo(dados_modos, MODO_TIME_ATTACK, pts,
                                      extra=f"{TIME_ATTACK_DURACAO}s")
                acao = tela_resultado_modo(MODO_TIME_ATTACK, pts, dados_modos,
                                           extra_info=f"Tempo: {TIME_ATTACK_DURACAO}s")
                estado = "jogo_modo" if acao == "jogar" else "menu"

            elif modo_atual == MODO_BOSS_RUSH:
                pts, fase = jogo_boss_rush(dados, dados_modos)
                total = len(Boss.FASES)
                venceu_tudo = (fase >= total)
                extra = f"Fase {min(fase+1, total)}/{total}" + (" - COMPLETO!" if venceu_tudo else "")
                registrar_placar_modo(dados_modos, MODO_BOSS_RUSH, pts, extra=extra)
                acao = tela_resultado_modo(MODO_BOSS_RUSH, pts, dados_modos,
                                           extra_info=extra, cor_modo=MAGENTA)
                estado = "jogo_modo" if acao == "jogar" else "menu"

            elif modo_atual == MODO_MULTI_VS:
                p1_pts, p2_pts, vencedor = jogo_multi(dados, dados_modos, modo_atual)
                pts_total = p1_pts + p2_pts
                extra = f"P1:{p1_pts}  P2:{p2_pts}"
                registrar_placar_modo(dados_modos, modo_atual, max(p1_pts,p2_pts), extra=extra)
                # Tela de vitória multiplayer
                acao = tela_vitoria_multi(vencedor, p1_pts, p2_pts, modo_atual)
                if acao == "jogar":
                    estado = "jogo_modo"
                else:
                    estado = "menu"
            else:
                estado = "menu"

        elif estado == "gameover":
            pts, niv, sp, dur = resultado_jogo
            # Tela de estatísticas detalhadas primeiro
            tela_stats_partida(pts, niv, dur, sp, dados)
            acao = game_over_screen(pts, niv, dados, sp, dur)
            if acao == "jogar":
                estado = "jogo"
            else:
                estado = "menu"


if __name__ == "__main__":
    main()
