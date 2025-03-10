from PIL import Image, ImageDraw, ImageFont
import os

def criar_splash_logo():
    """Cria uma imagem de splash básica para a aplicação"""
    
    # Dimensões da imagem
    width, height = 500, 300
    
    # Criar uma imagem transparente
    img = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Adicionar um retângulo arredondado semi-transparente como fundo
    # Primeiro criamos uma máscara para os cantos arredondados
    radius = 20
    
    # Desenhar o retângulo com cantos arredondados
    draw.rectangle(
        [(10, 10), (width-10, height-10)],
        fill=(240, 240, 240, 200),
        outline=(0, 120, 215, 255),
        width=2
    )
    
    # Adicionar título
    try:
        # Tentar carregar uma fonte do sistema
        titulo_font = ImageFont.truetype("arial.ttf", 48)
    except:
        # Usar fonte padrão se não encontrar
        titulo_font = ImageFont.load_default()
    
    draw.text(
        (width//2, height//2 - 50),
        "Remessa B3",
        fill=(0, 120, 215, 255),
        font=titulo_font,
        anchor="mm"
    )
    
    # Adicionar subtítulo
    try:
        subtitulo_font = ImageFont.truetype("arial.ttf", 24)
    except:
        subtitulo_font = ImageFont.load_default()
    
    draw.text(
        (width//2, height//2 + 10),
        "Gerador de Arquivo",
        fill=(100, 100, 100, 255),
        font=subtitulo_font,
        anchor="mm"
    )
    
    # Adicionar linha decorativa
    draw.line(
        [(width//4, height//2 + 40), (width*3//4, height//2 + 40)],
        fill=(0, 120, 215, 255),
        width=2
    )
    
    # Salvar a imagem
    img.save("splashLogo.png")
    print(f"Imagem de splash criada com sucesso: {os.path.abspath('splashLogo.png')}")

if __name__ == "__main__":
    criar_splash_logo() 