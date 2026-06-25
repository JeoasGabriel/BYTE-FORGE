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


