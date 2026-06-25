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


