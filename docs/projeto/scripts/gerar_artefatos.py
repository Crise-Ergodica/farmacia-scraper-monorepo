"""Gera dicionário e DER somente dos metadados ORM; não acessa banco nem .env.
Da raiz: PYTHONPATH=backend backend/.venv/bin/python docs/projeto/scripts/gerar_artefatos.py
Requer Graphviz (dot). Diagramas manuais .dot são preservados e recompilados.
"""
from pathlib import Path
import json
import subprocess
import tempfile
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from app.models import Base

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures'
SRC = FIG / 'fontes'

def esc(s):
    return str(s).replace('\\', r'\textbackslash{}').replace('_', r'\_').replace('&', r'\&').replace('%', r'\%').replace('#', r'\#').replace('{', r'\{').replace('}', r'\}')

def code(s):
    # \nolinkurl permite quebras nos identificadores longos sem mudar a grafia.
    return r'\ident{' + str(s) + '}'

meaning = {
'id':'Identificador do registro.', 'ean':'Código EAN da base oficial.',
'codigo_barras':'EAN/GTIN do item; pode estar ausente.', 'name_search':'Nome utilizado nas pesquisas.',
'principio_ativo':'Princípio ativo informado pela fonte.', 'laboratorio':'Laboratório informado.',
'exige_receita':'Indicador legado de exigência de receita.', 'categoria_regulatoria':'Categoria regulatória identificada na fonte.',
'referencia_anvisa':'Indicador de medicamento de referência.', 'exige_receita_confirmada':'Exigência de receita confirmada na fonte.',
'controle_especial':'Indicador de controle especial.', 'classificacao_fonte':'Procedência da classificação.',
'categorias':'Lista de categorias do catálogo.', 'imagem_url':'Referência externa da imagem; não armazena a fotografia.',
'imagem_fonte':'Origem da referência de imagem.', 'imagem_sku_origem':'SKU que sustenta a associação da imagem.',
'imagem_ean':'EAN usado como evidência da imagem.', 'imagem_match':'Tipo de correspondência de identidade.',
'imagem_status':'Estado de verificação da referência.', 'imagem_atualizada_em':'Instante de alteração da referência.',
'imagem_verificada_em':'Última validação bem-sucedida.', 'imagem_ultima_verificacao_em':'Instante da última tentativa de validação.',
'imagem_falhas_consecutivas':'Contador de falhas seguidas.', 'imagem_ultima_falha':'Descrição da falha recente.',
'imagem_motivo_rejeicao':'Motivo de rejeição da referência.', 'criado_em':'Instante de criação.',
'atualizado_em':'Instante da última atualização; ORM preenche ao alterar.', 'cnpj':'CNPJ da farmácia.',
'razao_social':'Razão social cadastrada.', 'nome_fantasia':'Nome comercial da farmácia.',
'telefone':'Contato telefônico.', 'endereco_completo':'Endereço cadastrado.', 'latitude':'Latitude do estabelecimento.',
'longitude':'Longitude do estabelecimento.', 'sku_interno':'Identificador do produto na farmácia; não é EAN.',
'preco':'Preço observado, com duas casas decimais.', 'quantidade_estoque':'Quantidade informada pela coleta, sem garantia de estoque físico.',
'disponivel':'Disponibilidade observada na fonte.', 'url_origem':'Página pública de origem da oferta.',
'observado_em':'Instante da observação da oferta.', 'farmacia_id':'Vínculo com a farmácia.',
'catalogo_id':'Vínculo com o item do catálogo.', 'medicamento_id':'Vínculo com o item do catálogo.',
'oferta_id':'Oferta associada à observação; registros legados podem não ter vínculo.',
'origem':'Origem da observação de preço.', 'data_registro':'Instante do registro histórico, sem fuso no banco.',
'nome':'Nome cadastrado do usuário.', 'email':'E-mail de autenticação.', 'hashed_password':'Resumo criptográfico da senha; nunca resposta pública.',
'is_active':'Indicador de conta ativa.', 'is_superuser':'Indicador de privilégio administrativo.',
'is_verified':'Indicador de verificação da conta.', 'usuario_id':'Vínculo com o usuário.',
'tarja':'Classificação de tarja informada.', 'registro_anvisa':'Identificador de registro na Anvisa.',
'status_registro':'Situação do registro na fonte.', 'fonte_classificacao':'Procedência da classificação oficial.',
'atualizado_fonte_em':'Data de atualização informada pela fonte.'}
summary = {'catalogo_base':'Identidade e classificação dos produtos e referências de imagens.',
'farmacias':'Cadastro dos estabelecimentos e coordenadas.', 'ofertas_farmacia':'Ocorrências comerciais de produtos em farmácias.',
'historico_precos':'Observações de preço vinculadas a produto e farmácia.',
'anvisa_medicamentos':'Base local de consulta oficial; cruzamento por EAN na aplicação, sem FK para o catálogo.',
'usuario':'Conta; nome é declarado localmente e os demais campos são herdados de SQLAlchemyBaseUserTableUUID.',
'usuario_farmacia_favorita':'Associação de usuários com farmácias favoritas, sem coluna id própria.',
'usuario_medicamento_favorito':'Associação de usuários com medicamentos favoritos, sem coluna id própria.'}
lines=[r'% Gerado por scripts/gerar_artefatos.py; não editar manualmente.',
 r'\subsection{Dicionário de dados}\label{sec:dicionario}',
 'A descrição representa os metadados ORM do checkout revisado, compilados para PostgreSQL. Nulo indica se a coluna admite SQL NULL; PK é chave primária e FK é chave estrangeira. Padrões Python são aplicados pela aplicação e não equivalem a padrões SQL. Não há consulta a um banco em execução.']
data={}
for t in Base.metadata.sorted_tables:
    data[t.name]=[]
    lines += [r'\subsubsection{'+esc(t.name)+'}'+r'\label{dic:'+t.name+'}', summary[t.name],
        r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}',
        r'\begin{longtable}{|>{\raggedright\arraybackslash}p{0.27\textwidth}|>{\raggedright\arraybackslash}p{0.22\textwidth}|>{\raggedright\arraybackslash}p{0.43\textwidth}|}',
        r'\caption{Dicionário: '+esc(t.name)+r'}\label{qua:dic-'+t.name+r'}\\\hline',
        r'\textbf{Coluna} & \textbf{Tipo / nulo} & \textbf{Descrição e restrições} \\\hline\endfirsthead',
        r'\multicolumn{3}{l}{Quadro \thequadro\ -- continuação}\\\hline',
        r'\textbf{Coluna} & \textbf{Tipo / nulo} & \textbf{Descrição e restrições} \\\hline\endhead',
        r'\multicolumn{3}{r}{Continua na próxima página.}\\\endfoot',
        r'\multicolumn{3}{l}{Fonte: metadados ORM do projeto (2026).}\\\endlastfoot']
    for c in t.columns:
        typ=c.type.compile(dialect=dialect()).replace('TIMESTAMP WITH TIME ZONE','timestamp com fuso').replace('TIMESTAMP WITHOUT TIME ZONE','timestamp sem fuso')
        rules=[]
        if c.primary_key: rules.append('PK'+(' composta' if len(t.primary_key.columns)>1 else ''))
        for fk in c.foreign_keys:
            rules.append('FK '+code(fk.target_fullname)+('. ON DELETE '+fk.ondelete if fk.ondelete else ''))
        unique=c.unique or any(i.unique and list(i.columns)==[c] for i in t.indexes) or any(isinstance(u,UniqueConstraint) and list(u.columns)==[c] for u in t.constraints)
        if unique: rules.append('único')
        if c.server_default is not None: rules.append('padrão SQL: '+code(c.server_default.arg))
        if c.default is not None:
            v=c.default.arg
            rules.append('padrão Python: '+code(getattr(v,'__name__',v)))
        text=meaning[c.name]+(' '+('; '.join(rules))+'.' if rules else '')
        lines.append(code(c.name)+' & '+esc(typ)+' / '+('sim' if c.nullable else 'não')+' & '+text+r' \\\hline')
        data[t.name].append({'coluna':c.name,'tipo_postgresql':str(c.type.compile(dialect=dialect())),'nulo':c.nullable,'pk':c.primary_key,'fk':[f.target_fullname for f in c.foreign_keys]})
    lines += [r'\end{longtable}\endgroup']
lines.insert(1,r'\begingroup\def\LTcaptype{quadro}')
lines.append(r'\endgroup')
(ROOT/'capitulos/02-dicionario.tex').write_text('\n'.join(lines)+'\n')
(SRC/'esquema-orm.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
# DER: atributos-chave aqui; todos os demais aparecem no dicionário.
dot=['digraph DER {','graph [rankdir=TB, nodesep=0.35, ranksep=0.7, bgcolor="white"];','node [shape=record, fontname="Helvetica", fontsize=14];','edge [fontname="Helvetica", fontsize=11, dir=none];']
for t in Base.metadata.sorted_tables:
    attrs=[]
    for c in t.columns:
        if c.primary_key or c.foreign_keys:
            attrs.append(c.name+(' [PK]' if c.primary_key else '')+(' [FK]' if c.foreign_keys else '')+(' (opcional)' if c.nullable else ''))
    dot.append(f'{t.name} [label="{{{t.name}|'+r'\l'.join(attrs)+r'\l}" ];')
    for c in t.columns:
        for f in c.foreign_keys:
            target=f.target_fullname.split('.')[0]
            dot.append(f'{target} -> {t.name} [taillabel="'+('0..1' if c.nullable else '1')+'", headlabel="0..*", labeldistance=1.7];')
dot.append('}')
(SRC/'der.dot').write_text('\n'.join(dot)+'\n')
for p in SRC.glob('*.dot'):
    if p.stem == 'diagrama-caso-de-uso':
        continue
    with tempfile.TemporaryDirectory(prefix='pi-diagrama-') as temp:
        intermediate = Path(temp) / 'graph.pdf'
        renderer = ['dot']
        subprocess.run(renderer + ['-Tpdf', str(p), '-o', str(intermediate)], check=True)
        # PDF 1.5 é compatível com o backend PDF do bundle Tectonic utilizado.
        subprocess.run(['gs', '-q', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite',
                        '-dCompatibilityLevel=1.5', '-sOutputFile='+str(FIG/(p.stem+'.pdf')),
                        str(intermediate)], check=True)
subprocess.run(['python3', str(SRC/'diagrama-caso-de-uso.py')], check=True)
print(f'{len(data)} tabelas; {sum(map(len,data.values()))} colunas; dicionário e diagramas gerados.')
