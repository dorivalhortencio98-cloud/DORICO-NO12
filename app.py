"""DORICO NO12 PRO: painel exploratório pré-jogo e acompanhamento de placares."""
from datetime import date, timedelta
from pathlib import Path
import streamlit as st
from futebol200.provider import get, APIError
from futebol200.engine import _team_samples, match_probabilities, analyze

st.set_page_config(page_title='DORICO NO12 PRO', page_icon='⚽', layout='wide')
st.markdown("""<style>
.stApp {background: radial-gradient(ellipse at 80% 0%, #172d43 0%, #0b111b 40%, #090e16 100%); color:#f3f7ff}
.block-container {max-width:1280px; padding-top:.7rem; padding-bottom:3rem}
.hero {padding:28px 30px; border:1px solid #263c55; border-radius:22px; background:linear-gradient(110deg,#162e49,#0d1726 72%); margin-bottom:22px; box-shadow:0 14px 42px #0003}
.hero .eyebrow {color:#64e6d0;font-size:12px;font-weight:800;letter-spacing:2px}
.hero h1 {font-size:40px;line-height:1.2;margin:10px 0;color:white}
.hero p {color:#b8cadc;margin:0;font-size:15px}
.section-title {font-size:22px;font-weight:800;color:white;margin:24px 0 12px}
.pick {background:linear-gradient(135deg,#16273b,#101c2c);border:1px solid #294360;border-radius:18px;padding:20px 22px;margin:12px 0;box-shadow:0 8px 22px #0002}
.pick.first {border-color:#24ff99;box-shadow:0 0 18px #24ff9950,0 10px 28px #0004}
.pick .rank {color:#67dfcc;font-size:12px;letter-spacing:1px;font-weight:800}
.pick .market {font-size:22px;font-weight:800;color:#fff;margin:7px 0}
.pick .pct {font-size:36px;font-weight:900;color:#65ffad;text-shadow:0 0 14px #24ff9955}
.pick .odd {color:#c5d7e7;font-size:14px}
.pick .bar {height:8px;background:#293d51;border-radius:20px;overflow:hidden;margin:14px 0 8px}
.pick .fill {height:100%;background:linear-gradient(90deg,#2cb8e5,#42e0ae);border-radius:20px}
.stButton>button[kind=primary] {background:linear-gradient(100deg,#08a86b,#11b9c9,#8b36e8);border:1px solid #58f4dc;border-radius:12px;padding:12px 25px;font-weight:800;box-shadow:0 0 16px #19d4ba44;transition:transform .18s, box-shadow .18s}.stButton>button[kind=primary]:hover {transform:translateY(-2px);box-shadow:0 0 26px #19d4ba88} .stTabs [data-baseweb="tab"] {font-weight:800;border-radius:12px 12px 0 0;padding:12px 24px}.stTabs [aria-selected="true"] {color:#55ffbf!important;text-shadow:0 0 10px #39ff8855} .neon-banner img {border-radius:18px;box-shadow:0 0 26px #1bdbd955;border:1px solid #19d7b4}
[data-testid="stMetric"] {background:#142337;border-radius:14px;padding:14px}
</style>""",unsafe_allow_html=True)
# Banner ilustrativo: os botões desenhados na arte são decorativos.
# A navegação funcional permanece nas abas Streamlit logo abaixo.
banner_path = Path(__file__).resolve().parent / 'assets' / 'dorico_no12_neon_banner.webp'
if banner_path.exists():
    st.image(str(banner_path), use_container_width=True)
else:
    st.title('⚽ DORICO NO12 PRO')
st.caption('⚡ Escolha a partida, clique em ANALISAR JOGO e veja as quatro maiores probabilidades estimadas.')
COMP = {'Brasileirão':'BSA','Premier League':'PL','La Liga':'PD','Serie A (Itália)':'SA','Bundesliga':'BL1','Ligue 1':'FL1','Portugal':'PPL','Holanda':'DED','Championship':'ELC','Champions League':'CL'}
LABELS = {'home_win':'Vitória mandante','draw':'Empate','away_win':'Vitória visitante',
'double_chance_1x':'Dupla chance 1X','double_chance_x2':'Dupla chance X2',
'btts_yes':'Ambas marcam — sim','btts_no':'Ambas marcam — não'}
for t in (0.5,1.5,2.5,3.5,4.5):
    LABELS[f'over_{t}']=f'Mais de {str(t).replace(".",",")} gols'
    LABELS[f'under_{t}']=f'Menos de {str(t).replace(".",",")} gols'

@st.cache_data(ttl=90, show_spinner=False)
def fixtures(code, start, end):
    return get(f'/competitions/{code}/matches?dateFrom={start}&dateTo={end}').get('matches',[])

@st.cache_data(ttl=3600, show_spinner=False)
def history(code):
    return get(f'/competitions/{code}/matches?status=FINISHED').get('matches',[])

@st.cache_data(ttl=60, show_spinner=False)
def live_all():
    # LIVE inclui IN_PLAY e PAUSED na API v4. Consulta global em uma requisição.
    return get('/matches?status=LIVE').get('matches', [])

def team_name(m, side):
    return (m.get(side) or {}).get('shortName') or (m.get(side) or {}).get('name') or 'Equipe'

def title(m):
    return f'{team_name(m,"homeTeam")} × {team_name(m,"awayTeam")} • {(m.get("utcDate") or "")[:16].replace("T"," ")} UTC'

def probabilities_for_game(m, matches):
    hid=(m.get('homeTeam') or {}).get('id')
    aid=(m.get('awayTeam') or {}).get('id')
    if not hid or not aid:
        return None, 0, 0, 'Equipes não identificadas pela API.'
    kickoff=m.get('utcDate') or ''
    past=[x for x in matches if x.get('status')=='FINISHED' and (x.get('utcDate') or '') < kickoff and x.get('id') != m.get('id')]
    home=_team_samples(past,hid,True)[:10]
    away=_team_samples(past,aid,False)[:10]
    if len(home)<5 or len(away)<5:
        return None,len(home),len(away),'Histórico insuficiente: são necessários pelo menos 5 jogos do mandante em casa e 5 do visitante fora.'
    ha=sum(x[1] for x in home)/len(home)
    hd=sum(x[2] for x in home)/len(home)
    aa=sum(x[1] for x in away)/len(away)
    ad=sum(x[2] for x in away)/len(away)
    from futebol200.engine import match_probabilities
    return match_probabilities(max(.05,(ha+ad)/2),max(.05,(aa+hd)/2)),len(home),len(away),None


def show_analysis(m, matches, exclude_half=True):
    import html
    probs, nh, na, reason = probabilities_for_game(m, matches)
    st.markdown('<div class="section-title">🏆 TOP 4 • ANÁLISE DA PARTIDA</div>', unsafe_allow_html=True)
    st.markdown(f'**{title(m)}**')
    if probs is None:
        st.warning('Histórico insuficiente para estimar probabilidades desta partida.')
        st.write(reason)
        return
    selected=[(k,p) for k,p in probs.items() if not (exclude_half and k in ('over_0.5','under_0.5')) and 0<p<1]
    ranked=sorted(selected,key=lambda item:item[1],reverse=True)[:4]
    for i,(market,p) in enumerate(ranked,1):
        label=html.escape(LABELS.get(market,market))
        st.markdown(f'''<div class="pick {'first' if i==1 else ''}">
          <div class="rank">{'⭐ DESTAQUE ESTATÍSTICO' if i==1 else f'#{i} • PROBABILIDADE ESTIMADA'}</div>
          <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
            <div><div class="market">{label}</div><div class="odd">Odd justa teórica: <b>{1/p:.2f}</b></div></div>
            <div class="pct">{p*100:.1f}%</div>
          </div>
          <div class="bar"><div class="fill" style="width:{p*100:.1f}%"></div></div>
        </div>''',unsafe_allow_html=True)
    st.caption(f'📈 Base: {nh} jogos do mandante em casa e {na} do visitante fora. Modelo Poisson experimental; estimativas não calibradas nem validadas.')
    st.info('O ranking apresenta as maiores probabilidades estimadas entre os mercados selecionados, não as apostas com maior retorno esperado. Sem odds reais, não é possível avaliar valor de entrada.')
    with st.expander('📊 Ver todos os mercados e odds justas'):
        import pandas as pd
        rows=[{'Mercado':LABELS.get(k,k),'Probabilidade':f'{v:.1%}','Odd justa teórica':f'{1/v:.2f}'} for k,v in sorted(probs.items(),key=lambda x:x[1],reverse=True) if 0<v<1]
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)

choice=st.selectbox('Competição',list(COMP))
code=COMP[choice]
tab_pre,tab_live=st.tabs(['📅 Pré-jogo','🔴 Em andamento'])
now=date.today()
with tab_pre:
    d1,d2=st.columns(2)
    with d1: start=st.date_input('Data inicial',value=now,key='from')
    with d2: end=st.date_input('Data final',value=now+timedelta(days=7),key='to')
    if start>end:
        st.error('A data inicial deve ser anterior à final.')
    else:
        try:
            ms=[m for m in fixtures(code,start.isoformat(),end.isoformat()) if m.get('status') in ('SCHEDULED','TIMED')]
            if not ms: st.info('Nenhuma partida futura encontrada para esse período e competição.')
            else:
                game=st.selectbox('Escolha uma partida futura',ms,format_func=title,key='pre_game')
                exclude_half=st.checkbox('Ocultar mercados de 0,5 gol',value=True,help='Evita que mercados muito básicos dominem o ranking.')
                if st.button('🚀 ANALISAR JOGO', type='primary', use_container_width=True):
                    with st.spinner('Calculando probabilidades da partida...'):
                        show_analysis(game,history(code),exclude_half)

        except (APIError,ValueError) as e: st.error(str(e))
with tab_live:
    st.caption('Partidas ao vivo retornadas pela Football-Data.org. Atualização manual, conforme cobertura e plano da API.')
    scope=st.radio('Consultar', ['Todas as competições disponíveis', f'Somente {choice}'], horizontal=True)
    if st.button('🔄 Atualizar partidas ao vivo', type='primary'):
        live_all.clear()
    try:
        all_live=live_all()
        ms=all_live if scope.startswith('Todas') else [m for m in all_live if (m.get('competition') or {}).get('code') == code]
        if not ms:
            st.info('A API não retornou partidas ao vivo para este filtro agora. Isso pode significar ausência de jogos ou restrição de cobertura do plano; não é necessariamente um erro.')
            st.caption('Experimente “Todas as competições disponíveis” caso esteja consultando apenas um campeonato.')
        else:
            st.success(f'{len(ms)} partida(s) ao vivo retornada(s) pela API.')
            for m in sorted(ms,key=lambda x:(x.get('competition') or {}).get('name','')):
                comp=(m.get('competition') or {}).get('name','Competição')
                sc=m.get('score') or {}
                ft=sc.get('fullTime') or {}
                h=ft.get('home')
                a=ft.get('away')
                # Evitar afirmar minuto ou eventos não recebidos.
                minute=m.get('minute')
                moment=f' • {minute} min' if isinstance(minute,int) else ''
                st.markdown(f'**{comp}** — {team_name(m,"homeTeam")} **{h if h is not None else "–"} × {a if a is not None else "–"}** {team_name(m,"awayTeam")}  \nStatus: {m.get("status", "não informado")}{moment}')
        st.subheader('🎯 Seleção automática ao vivo')
        st.warning('📋 DADOS INSUFICIENTES — seleção automática ao vivo ainda indisponível.')
        st.caption('Esta API não fornece de forma confiável minuto, eventos e odds necessários para calcular e comparar probabilidades durante o jogo. O painel exibe placares quando recebidos, mas não transforma probabilidades pré-jogo em sinais ao vivo.')
    except (APIError,ValueError) as e:
        st.error(str(e))
        st.info('Se houver erro 403, confira a cobertura do seu plano na Football-Data.org; erro 429 indica limite de requisições.')

st.divider()
st.caption('⚽ DORICO NO12 PRO • Dados: Football-Data.org, conforme cobertura do plano • Probabilidades experimentais, sem garantia de acerto • Sem API paga adicional')
