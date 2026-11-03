"""Diagrama vetorial com posições explícitas para preservar fronteira e rótulos.
Da raiz: python3 docs/projeto/figures/fontes/diagrama-caso-de-uso.py
Requer Pycairo. Não usa rede, aplicação ou dados de usuários.
"""
from pathlib import Path
import math
import cairo

output = Path(__file__).resolve().parents[1] / 'diagrama-caso-de-uso.pdf'
surface = cairo.PDFSurface(str(output), 565, 650)
surface.restrict_to_version(cairo.PDF_VERSION_1_5)
c = cairo.Context(surface)
c.set_source_rgb(1, 1, 1); c.paint(); c.set_source_rgb(0, 0, 0)
c.set_line_width(0.8)
c.select_font_face('Helvetica')

def text(x, y, value, size=10.5):
    c.set_font_size(size)
    for i, line in enumerate(value.split('\n')):
        e = c.text_extents(line)
        c.move_to(x - e.width / 2 - e.x_bearing, y + i * (size + 2))
        c.show_text(line)

def line(x1,y1,x2,y2):
    c.move_to(x1,y1);c.line_to(x2,y2);c.stroke()

def actor(y, name):
    c.rectangle(5,y-20,140,40);c.stroke()
    text(75,y-4,'«actor»\n'+name,10.5)

def case(y, name, requirement, future=False):
    c.save();c.translate(350,y);c.scale(130,23);c.new_path()
    c.arc(0,0,1,0,2*math.pi);c.restore()
    if future: c.set_dash([4,3])
    c.stroke();c.set_dash([])
    text(350,y-2,name+'\n'+requirement,12)

c.rectangle(175,8,380,626);c.stroke()
text(365,25,'Plataforma Preço Bão — escopo previsto',12)
# Associações sem setas; nenhuma autenticação implícita por include.
for y in (65,195,255,315,375,435): line(145,285,220,y)
line(145,495,220,515);line(145,555,220,515)
line(145,555,220,590);line(145,610,220,590)
actor(285,'Consumidor');actor(495,'Sites das farmácias')
actor(555,'Operador de coleta');actor(610,'Arquivo CMED/Anvisa')
for y,name,requirement,future in [
 (65,'Pesquisar produtos','RF04',False),
 (125,'Calcular distância','RF06 — previsto',True),
 (195,'Consultar cartões e ofertas','RF05',False),
 (255,'Gerenciar favoritos','RF07',False),
 (315,'Consultar histórico','RF08',False),
 (375,'Cadastrar / autenticar / perfil','RF03',False),
 (435,'Recuperar senha','RF03 — previsto',True),
 (515,'Coletar e persistir ofertas','RF01 / RF02',False),
 (590,'Ingerir base e enriquecer catálogo','RF02',False)]:
    case(y,name,requirement,future)
# Extend aponta para a busca; condição descrita no texto do documento.
c.set_dash([4,3]);c.move_to(480,125)
c.curve_to(510,125,510,65,480,65);c.stroke();c.set_dash([])
line(480,65,487,61);line(480,65,487,69)
text(530,97,'«extend»',10)
surface.finish()
print(output)
