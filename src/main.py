from game import Game
from notation import generate_fen
from pieces import Side
from config import AUTO_PROMO

def main():    
    game = Game()
    
    while True:
        print(game.board)
        
        jogada = None        
        lado = 'brancas' if game.status.side == Side.WHITE else 'pretas'
        print(f"\nJogam as {lado}")
                
        while True:
            entrada = input("lance (ou 'sair'): ").strip()   
            if entrada == 'sair':
                break   
              
            if entrada == 'fen':
                print(generate_fen(game.board.grid, game.status)+"\n")
                continue
                          
            jogada = entrada.split()
            if len(jogada) != 2:
                print("Erro: informe origem e destino, ex: 'e2 e4'\n")
                continue
            
            if jogada is not None:
                try:
                    if not AUTO_PROMO and game.will_promote(*jogada):
                        options = "Q R B N" if game.status.side == Side.WHITE else "q r b n"
                        promotion = input(f"escolha a peça a promover ({options}): ")                        
                        game.play(*jogada, promotion)
                    else:
                        game.play(*jogada)
                        
                    print()
                    break
                except ValueError as erro:
                    print(f"Erro: {erro}\n")  
                                                             
        if entrada == 'sair':
            break
    
    
if __name__ == "__main__":
    main()