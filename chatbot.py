# chatbot.py
import spacy
import re
import streamlit as st
import pdfplumber
from docx import Document

# Carrega o modelo de NLP em português do spaCy
nlp = spacy.load("pt_core_news_lg")

def extrair_texto_arquivo(uploaded_file):
    """Extrai texto de arquivos PDF, DOCX ou TXT"""
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                return "\n".join([page.extract_text() for page in pdf.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            st.error("Formato de arquivo não suportado")
            return None
    except Exception as e:
        st.error(f"Erro ao extrair texto: {str(e)}")
        return None

def analisar_contrato(texto):
    """Analisa o contrato e identifica cláusulas importantes"""
    doc = nlp(texto)
    
    resultados = {
        "velocidade_contratada": None,
        "minimo_garantido": None,
        "conformidade_velocidade": None,
        "prazo_fidelidade": None,
        "multa_cancelamento": None,
        "clausulas_abusivas": [],
        "politica_privacidade": False
    }

    # Análise de velocidade da internet
    try:
        match_velocidade = re.search(r"(\d+)\s*Mbps", texto, re.IGNORECASE)
        if match_velocidade:
            velocidade = int(match_velocidade.group(1))
            resultados["velocidade_contratada"] = velocidade
            
            # Verificação ANATEL (70% mínimo)
            minimo_regulatorio = velocidade * 0.7
            resultados["minimo_garantido"] = minimo_regulatorio
            resultados["conformidade_velocidade"] = "Conforme" if minimo_regulatorio <= velocidade else "Inconforme"
    except Exception as e:
        st.error(f"Erro na análise de velocidade: {str(e)}")

    # Análise de prazo de fidelidade
    try:
        match_fidelidade = re.search(r"(\d+)\s+(meses|anos)", texto)
        if match_fidelidade:
            resultados["prazo_fidelidade"] = f"{match_fidelidade.group(1)} {match_fidelidade.group(2)}"
    except:
        pass

    # Análise de multa por cancelamento
    try:
        match_multa = re.search(r"multa\s+de\s+(\d+%|\d+\s*R\$)", texto, re.IGNORECASE)
        if match_multa:
            resultados["multa_cancelamento"] = match_multa.group(1)
    except:
        pass

    # Detecção de cláusulas abusivas
    try:
        termos_abusivos = [
            "unilateralmente", 
            "alteração de preço",
            "proibido cancelar",
            "exclusiva responsabilidade",
            "vedado ao consumidor"
        ]
        
        for sent in doc.sents:
            if any(palavra in sent.text.lower() for palavra in termos_abusivos):
                resultados["clausulas_abusivas"].append(sent.text)
    except:
        pass

    # Verificação de menção à LGPD
    try:
        resultados["politica_privacidade"] = any(
            ent.text.lower() in ["lgpd", "lei geral de proteção de dados"] 
            for ent in doc.ents
        )
    except:
        pass

    return resultados

# Configuração da interface Streamlit
st.set_page_config(page_title="Analisador de Contratos de Internet", page_icon="📄")

st.title("🤖 Analisador Jurídico de Contratos de Internet")
st.markdown("""
**Instruções:**
1. Faça upload do seu contrato (PDF, DOCX ou TXT)
2. Aguarde a análise automática
3. Verifique os resultados
""")

uploaded_file = st.file_uploader("Selecione o arquivo", type=["pdf", "docx", "txt"])

if uploaded_file:
    texto = extrair_texto_arquivo(uploaded_file)
    
    if texto:
        with st.spinner("Analisando contrato..."):
            analise = analisar_contrato(texto)
        
        # Exibição dos resultados
        st.subheader("🔍 Resultados da Análise")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Velocidade Contratada", 
                     f"{analise['velocidade_contratada']} Mbps" if analise['velocidade_contratada'] else "Não encontrada")
            
            st.metric("Prazo de Fidelidade", 
                     analise['prazo_fidelidade'] or "Não especificado")
            
            st.metric("Multa por Cancelamento", 
                     analise['multa_cancelamento'] or "Não especificada")
        
        with col2:
            st.metric("Mínimo Garantido (ANATEL)", 
                     f"{analise['minimo_garantido']:.1f} Mbps" if analise['minimo_garantido'] else "N/A")
            
            st.metric("Conformidade Velocidade", 
                     analise['conformidade_velocidade'] or "N/A")
            
            if analise['politica_privacidade']:
                st.success("✅ Menção à LGPD encontrada")
            else:
                st.warning("⚠️ LGPD não mencionada")
        
        # Seção de cláusulas abusivas
        if analise['clausulas_abusivas']:
            st.subheader("🚨 Cláusulas Potencialmente Abusivas")
            for i, clausula in enumerate(analise['clausulas_abusivas'], 1):
                st.error(f"{i}. {clausula}")
        else:
            st.success("✅ Nenhuma cláusula potencialmente abusiva detectada")
        
        # Exibição parcial do texto
        st.subheader("📄 Texto Extraído (Trecho)")
        st.text(texto[:2000] + "...")  # Mostra apenas os primeiros 2000 caracteres

    else:
        st.error("Não foi possível extrair texto do arquivo")
else:
    st.info("⚠️ Por favor, faça upload de um arquivo para análise")